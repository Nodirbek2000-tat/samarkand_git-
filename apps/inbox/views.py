from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.core.permissions import IsSuperuser

from .models import Appeal, CooperationRequest, MemberApplication
from .serializers import (
    AppealAdminSerializer,
    AppealPublicSerializer,
    CooperationAdminSerializer,
    CooperationPublicSerializer,
    MemberApplicationAdminSerializer,
    MemberApplicationPublicSerializer,
)


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    return (forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")) or None


class InboxViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    POST is the public form (anyone, rate-limited).
    Reading and processing submissions is for administrators only.
    """

    public_serializer_class = None
    admin_serializer_class = None
    filterset_fields = ["status"]
    ordering_fields = ["created_at", "status"]
    throttle_scope = "public_forms"

    def get_permissions(self):
        return [AllowAny()] if self.action == "create" else [IsSuperuser()]

    def get_throttles(self):
        return [ScopedRateThrottle()] if self.action == "create" else []

    def get_serializer_class(self):
        return self.public_serializer_class if self.action == "create" else self.admin_serializer_class

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = request.user if request.user.is_authenticated else None
        ser.save(ip_address=client_ip(request), user=user)
        return Response(
            {"ok": True, "detail": "Rahmat! Murojaatingiz qabul qilindi. Tez orada siz bilan bog‘lanamiz."},
            status=status.HTTP_201_CREATED,
        )

    notify_label = "Murojaatingiz"
    telegram_queued = None

    def update(self, request, *args, **kwargs):
        self.telegram_queued = None
        response = super().update(request, *args, **kwargs)
        # tells the panel whether a Telegram message was queued for the bot (None = nothing to send)
        response.data["telegram_queued"] = self.telegram_queued
        return response

    def perform_update(self, serializer):
        before = serializer.instance
        old_reply, old_status = before.reply, before.status
        extra = {"handled_by": self.request.user}
        new_reply = serializer.validated_data.get("reply", old_reply)
        if new_reply and new_reply != old_reply:
            extra["replied_at"] = timezone.now()
        obj = serializer.save(**extra)

        # tell a registered sender about the answer / resolution through the Telegram bot
        if obj.user_id and (new_reply != old_reply or (obj.status != old_status and obj.status == "done")):
            from apps.accounts.telegram import esc, notify

            lines = [f"📬 <b>{self.notify_label} bo‘yicha yangilik</b>", f"Holati: <b>{obj.get_status_display()}</b>"]
            if obj.reply:
                lines += ["", esc(obj.reply)]
            lines += ["", "Batafsil — saytdagi shaxsiy kabinetingizda."]
            self.telegram_queued = notify(obj.user, "\n".join(lines))


class AppealViewSet(InboxViewSet):
    queryset = Appeal.objects.select_related("handled_by", "user__telegram")
    public_serializer_class = AppealPublicSerializer
    admin_serializer_class = AppealAdminSerializer
    filterset_fields = ["status", "kind"]
    search_fields = ["full_name", "phone", "email", "organization", "subject", "message"]


class CooperationRequestViewSet(InboxViewSet):
    notify_label = "Hamkorlik taklifingiz"
    queryset = CooperationRequest.objects.select_related("handled_by", "user__telegram")
    public_serializer_class = CooperationPublicSerializer
    admin_serializer_class = CooperationAdminSerializer
    filterset_fields = ["status", "kind"]
    search_fields = ["organization", "contact_person", "phone", "email", "proposal"]


class MemberApplicationViewSet(InboxViewSet):
    notify_label = "A’zolik arizangiz"
    queryset = MemberApplication.objects.select_related("handled_by", "user__telegram")
    public_serializer_class = MemberApplicationPublicSerializer
    admin_serializer_class = MemberApplicationAdminSerializer
    filterset_fields = ["status", "size"]
    search_fields = ["full_name", "company", "phone", "email", "industry"]
