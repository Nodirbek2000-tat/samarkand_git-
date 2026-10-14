"""
Internal API for the Telegram bot (../samarkand_bot).

Every request must carry `X-Bot-Secret: <BOT_API_SECRET>`; without the setting the API is closed.
These endpoints are not for browsers: no session, no CSRF, no throttling, excluded from the schema.
"""

import hmac

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.revalidate import notify_frontend

from . import telegram
from .models import BotMessage, BotState, TelegramAccount


class HasBotSecret(BasePermission):
    def has_permission(self, request, view):
        expected = settings.BOT_API_SECRET
        given = request.headers.get("X-Bot-Secret", "")
        return bool(expected) and hmac.compare_digest(given.encode(), expected.encode())


class BotAPIView(APIView):
    permission_classes = [HasBotSecret]
    authentication_classes = []
    throttle_classes = []


class TelegramUserSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    chat_id = serializers.IntegerField(required=False)
    username = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    first_name = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")
    last_name = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")


class RegisterSerializer(TelegramUserSerializer):
    chat_id = serializers.IntegerField()
    phone = serializers.CharField(max_length=32)


def _code_response(account: TelegramAccount, **extra) -> Response:
    """Shared tail of register/code: blocked → 403, too soon → 429, otherwise a fresh code."""
    if not account.user.is_active:
        return Response({"detail": "blocked"}, status=status.HTTP_403_FORBIDDEN)
    try:
        code = telegram.issue_code(account)
    except telegram.CodeCooldown as exc:
        return Response({"detail": "cooldown", "retry_after": exc.retry_after, **extra}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    return Response(
        {
            "code": code,
            "ttl": settings.TELEGRAM_LOGIN_CODE_TTL,
            "name": account.user.get_full_name() or account.first_name,
            **extra,
        }
    )


class BotHelloView(BotAPIView):
    """Called once on bot start-up with getMe() data — the site learns the bot's username from here."""

    @extend_schema(exclude=True)
    def post(self, request):
        username = str(request.data.get("username", ""))[:64].lstrip("@")
        state = BotState.get()
        changed = state.username != username
        state.username = username
        state.first_name = str(request.data.get("first_name", ""))[:128]
        state.started_at = state.last_seen_at = timezone.now()
        state.save()
        if changed:
            notify_frontend(["settings"])  # the /kirish page shows the bot link
        return Response({"ok": True, "pending": BotMessage.objects.filter(status=BotMessage.Status.PENDING).count()})


class BotRegisterView(BotAPIView):
    """The user shared their own contact in the bot: register (or refresh) them and hand out a code."""

    @extend_schema(exclude=True)
    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        account, created = telegram.register(**ser.validated_data)
        return _code_response(account, created=created)


class BotCodeView(BotAPIView):
    """A registered user asks for a new sign-in code. 404 means: ask them for their phone number first."""

    @extend_schema(exclude=True)
    def post(self, request):
        ser = TelegramUserSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        account = TelegramAccount.objects.select_related("user").filter(telegram_id=data["telegram_id"]).first()
        if account is None:
            return Response({"detail": "not_registered"}, status=status.HTTP_404_NOT_FOUND)
        telegram.touch(account, chat_id=data.get("chat_id"), username=data.get("username"))
        return _code_response(account)


class BotMemberView(BotAPIView):
    """The user blocked (or unblocked) the bot — stop queueing messages they would never get."""

    @extend_schema(exclude=True)
    def post(self, request):
        try:
            telegram_id = int(request.data.get("telegram_id"))
        except (TypeError, ValueError):
            return Response({"detail": "telegram_id kerak"}, status=status.HTTP_400_BAD_REQUEST)
        blocked = bool(request.data.get("blocked"))
        updated = TelegramAccount.objects.filter(telegram_id=telegram_id).update(is_blocked_bot=blocked)
        return Response({"ok": True, "known": bool(updated)})


class BotOutboxView(BotAPIView):
    """Messages waiting for delivery. Polling this endpoint is also the bot's heartbeat."""

    @extend_schema(exclude=True)
    def get(self, request):
        BotState.objects.update_or_create(pk=1, defaults={"last_seen_at": timezone.now()})
        try:
            limit = max(1, min(int(request.query_params.get("limit", 30)), 100))
        except ValueError:
            limit = 30
        rows = BotMessage.objects.filter(status=BotMessage.Status.PENDING).values("id", "chat_id", "text")[:limit]
        return Response({"messages": list(rows)})


class BotOutboxAckView(BotAPIView):
    """Delivery report for one outbox message."""

    @extend_schema(exclude=True)
    @transaction.atomic
    def post(self, request, pk):
        msg = BotMessage.objects.select_for_update().filter(pk=pk).first()
        if msg is None:
            return Response({"detail": "not_found"}, status=status.HTTP_404_NOT_FOUND)
        if request.data.get("ok"):
            msg.status, msg.sent_at, msg.last_error = BotMessage.Status.SENT, timezone.now(), ""
            msg.attempts = F("attempts") + 1
            msg.save(update_fields=["status", "sent_at", "last_error", "attempts"])
            return Response({"ok": True})

        msg.attempts += 1
        msg.last_error = str(request.data.get("error", ""))[:255]
        blocked = bool(request.data.get("blocked"))
        if blocked or msg.attempts >= BotMessage.MAX_ATTEMPTS:
            msg.status = BotMessage.Status.FAILED
        msg.save(update_fields=["status", "attempts", "last_error"])
        if blocked and msg.account_id:
            TelegramAccount.objects.filter(pk=msg.account_id).update(is_blocked_bot=True)
        return Response({"ok": True, "status": msg.status})
