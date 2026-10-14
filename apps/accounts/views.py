from itertools import chain

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.db.models import Count, IntegerField, Value
from django.db.models.functions import Coalesce
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.permissions import IsStaff, IsSuperuser, is_admin
from apps.inbox.models import Appeal, CooperationRequest, MemberApplication
from apps.inbox.serializers import MySubmissionSerializer

from .models import LoginCode
from .serializers import (
    ChangePasswordSerializer,
    CodeSerializer,
    LoginSerializer,
    MeSerializer,
    ProfileSerializer,
    UserAdminSerializer,
)
from .telegram import bot_username

User = get_user_model()


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses={200: dict})
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


@method_decorator(ensure_csrf_cookie, name="dispatch")
class MeView(APIView):
    """Current visitor or staff member. `is_staff` decides access to the admin panel."""

    permission_classes = [AllowAny]

    @extend_schema(responses={200: dict})
    def get(self, request):
        user = request.user
        if not (user.is_authenticated and user.is_active):
            return Response({"authenticated": False, "user": None})
        return Response({"authenticated": True, "user": MeSerializer(user).data})


class LoginView(APIView):
    """Username + password sign-in — for staff (admin panel) only."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(request=LoginSerializer, responses={200: MeSerializer})
    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = authenticate(request, **ser.validated_data)
        if user is None:
            return Response({"detail": "Login yoki parol noto‘g‘ri."}, status=status.HTTP_400_BAD_REQUEST)
        if not is_admin(user):
            return Response({"detail": "Bu hisobda administrator huquqi yo‘q."}, status=status.HTTP_403_FORBIDDEN)
        login(request, user)
        return Response({"authenticated": True, "user": MeSerializer(user).data})


class LogoutView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(APIView):
    permission_classes = [IsStaff]

    @extend_schema(request=ChangePasswordSerializer, responses={204: None})
    def post(self, request):
        ser = ChangePasswordSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        request.user.set_password(ser.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        update_session_auth_hash(request, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------ Telegram sign-in

class TelegramConfigView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses={200: dict})
    def get(self, request):
        username = bot_username()
        return Response(
            {
                "enabled": bool(username and settings.BOT_API_SECRET),
                "bot_username": username,
                "bot_url": f"https://t.me/{username}?start=login" if username else "",
                "code_ttl": settings.TELEGRAM_LOGIN_CODE_TTL,
            }
        )


class TelegramCodeLoginView(APIView):
    """Exchange the 6-digit code from the bot for a session (registration happens in the bot)."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "telegram_code"

    @extend_schema(request=CodeSerializer, responses={200: MeSerializer})
    def post(self, request):
        ser = CodeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        account = LoginCode.redeem(ser.validated_data["code"])
        if account is None:
            return Response(
                {"detail": "Kod noto‘g‘ri yoki muddati o‘tgan. Botdan yangi kod oling."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = account.user
        if not user.is_active:
            return Response({"detail": "Hisobingiz bloklangan. Kengash bilan bog‘laning."}, status=status.HTTP_403_FORBIDDEN)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        if not user.is_staff:
            request.session.set_expiry(settings.SITE_USER_SESSION_AGE)
        account.last_login_at = timezone.now()
        account.save(update_fields=["last_login_at"])
        return Response({"authenticated": True, "user": MeSerializer(user).data})


# ------------------------------------------------------------------ visitor cabinet

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: MeSerializer})
    def get(self, request):
        return Response(MeSerializer(request.user).data)

    @extend_schema(request=ProfileSerializer, responses={200: MeSerializer})
    def patch(self, request):
        ser = ProfileSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        user = request.user
        for field in ("first_name", "last_name", "email"):
            if field in data:
                setattr(user, field, data[field])
        user.save()
        tg = getattr(user, "telegram", None)
        if tg:
            for field in ("company", "position"):
                if field in data:
                    setattr(tg, field, data[field])
            tg.save()
        return Response(MeSerializer(user).data)


class MySubmissionsView(APIView):
    """Everything the signed-in visitor sent through the site forms, newest first."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: MySubmissionSerializer(many=True)})
    def get(self, request):
        user = request.user
        rows = chain(
            (
                {
                    "id": a.id, "type": "appeal", "type_label": a.get_kind_display(),
                    "title": a.subject or a.get_kind_display(), "message": a.message,
                    "status": a.status, "status_label": a.get_status_display(),
                    "reply": a.reply, "replied_at": a.replied_at, "created_at": a.created_at,
                }
                for a in Appeal.objects.filter(user=user)
            ),
            (
                {
                    "id": c.id, "type": "cooperation", "type_label": "Hamkorlik taklifi",
                    "title": c.organization, "message": c.proposal,
                    "status": c.status, "status_label": c.get_status_display(),
                    "reply": c.reply, "replied_at": c.replied_at, "created_at": c.created_at,
                }
                for c in CooperationRequest.objects.filter(user=user)
            ),
            (
                {
                    "id": m.id, "type": "membership", "type_label": "A’zolik arizasi",
                    "title": m.get_size_display(), "message": m.message,
                    "status": m.status, "status_label": m.get_status_display(),
                    "reply": m.reply, "replied_at": m.replied_at, "created_at": m.created_at,
                }
                for m in MemberApplication.objects.filter(user=user)
            ),
        )
        items = sorted(rows, key=lambda r: r["created_at"], reverse=True)
        return Response(MySubmissionSerializer(items, many=True).data)


# ------------------------------------------------------------------ administrators

class UserAdminViewSet(viewsets.ModelViewSet):
    """All accounts for administrators: search, filter by role, grant / revoke rights, block."""

    serializer_class = UserAdminSerializer
    permission_classes = [IsSuperuser]
    search_fields = ["username", "first_name", "last_name", "email", "telegram__phone", "telegram__username", "telegram__company"]
    ordering_fields = ["date_joined", "last_login", "username"]

    def get_queryset(self):
        zero = Value(0, output_field=IntegerField())
        qs = (
            User.objects.select_related("telegram")
            .annotate(
                submissions=Coalesce(Count("appeal_submissions", distinct=True), zero)
                + Coalesce(Count("cooperationrequest_submissions", distinct=True), zero)
                + Coalesce(Count("memberapplication_submissions", distinct=True), zero)
            )
            .order_by("-is_superuser", "-is_staff", "-date_joined")
        )
        role = self.request.query_params.get("role")
        if role == "admin":
            qs = qs.filter(is_superuser=True)
        elif role == "editor":
            qs = qs.filter(is_staff=True, is_superuser=False)
        elif role == "staff":
            qs = qs.filter(is_staff=True)
        elif role == "user":
            qs = qs.filter(is_staff=False)
        return qs

    @extend_schema(responses={200: dict})
    @action(detail=False)
    def counts(self, request):
        base = User.objects.all()
        return Response(
            {
                "all": base.count(),
                "admin": base.filter(is_superuser=True).count(),
                "editor": base.filter(is_staff=True, is_superuser=False).count(),
                "user": base.filter(is_staff=False).count(),
            }
        )

    def perform_destroy(self, instance):
        from rest_framework.exceptions import ValidationError

        if instance.pk == self.request.user.pk:
            raise ValidationError("O‘zingizni o‘chira olmaysiz.")
        if instance.is_superuser and not User.objects.filter(is_superuser=True, is_active=True).exclude(pk=instance.pk).exists():
            raise ValidationError("Bu oxirgi administrator.")
        # keep history (appeals, authorship) intact: deactivate instead of deleting
        instance.is_active = False
        instance.save(update_fields=["is_active"])
