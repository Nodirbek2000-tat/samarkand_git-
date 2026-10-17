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

from . import broadcast, telegram
from .models import BotBroadcast, BotChannel, BotMessage, BotState, BotSubscriber, TelegramAccount


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
        BotSubscriber.objects.filter(telegram_id=telegram_id).update(is_blocked=blocked)  # out of the audience too
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


# --------------------------------------------------------------------------------------- audience & broadcasts


class BotSeenView(BotAPIView):
    """Someone wrote to the bot: keep them in the audience. Tells the bot whether they may open /admin."""

    @extend_schema(exclude=True)
    def post(self, request):
        ser = TelegramUserSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        BotSubscriber.objects.update_or_create(
            telegram_id=d["telegram_id"],
            defaults={
                "chat_id": d.get("chat_id") or d["telegram_id"],
                "first_name": d["first_name"],
                "last_name": d["last_name"],
                "username": d["username"],
                "is_blocked": False,
                "last_seen_at": timezone.now(),
            },
        )
        return Response({"admin": broadcast.is_bot_admin(d["telegram_id"])})


class BotStatsView(BotAPIView):
    @extend_schema(exclude=True)
    def get(self, request):
        return Response(broadcast.stats())


class ChannelSerializer(serializers.ModelSerializer):
    link = serializers.CharField(read_only=True)

    class Meta:
        model = BotChannel
        fields = ["id", "chat_id", "title", "username", "invite_link", "link", "is_active"]


class BotChannelsView(BotAPIView):
    """Mandatory channels: the bot reads them often and adds one after checking it is an admin there."""

    @extend_schema(exclude=True)
    def get(self, request):
        return Response({"channels": ChannelSerializer(BotChannel.objects.filter(is_active=True), many=True).data})

    @extend_schema(exclude=True)
    def post(self, request):
        try:
            chat_id = int(request.data.get("chat_id"))
        except (TypeError, ValueError):
            return Response({"detail": "chat_id kerak"}, status=status.HTTP_400_BAD_REQUEST)
        channel, created = BotChannel.objects.update_or_create(
            chat_id=chat_id,
            defaults={
                "title": str(request.data.get("title", ""))[:255],
                "username": str(request.data.get("username", ""))[:64].lstrip("@"),
                "invite_link": str(request.data.get("invite_link", ""))[:200],
                "is_active": True,
            },
        )
        return Response({"channel": ChannelSerializer(channel).data, "created": created})


class BotChannelDeleteView(BotAPIView):
    @extend_schema(exclude=True)
    def delete(self, request, chat_id):
        deleted, _ = BotChannel.objects.filter(chat_id=chat_id).delete()
        return Response({"ok": bool(deleted)})


class BotBroadcastCreateView(BotAPIView):
    """An administrator sent an ad in the bot: copy that message to every subscriber."""

    @extend_schema(exclude=True)
    def post(self, request):
        try:
            from_chat_id = int(request.data["from_chat_id"])
            message_id = int(request.data["message_id"])
        except (KeyError, TypeError, ValueError):
            return Response({"detail": "from_chat_id va message_id kerak"}, status=status.HTTP_400_BAD_REQUEST)
        item = BotBroadcast.objects.create(
            kind=BotBroadcast.Kind.AD,
            title=str(request.data.get("title", ""))[:255] or "Reklama",
            from_chat_id=from_chat_id,
            message_id=message_id,
            created_by_chat=from_chat_id,
        )
        queued = BotBroadcast.objects.filter(status__in=[BotBroadcast.Status.PENDING, BotBroadcast.Status.SENDING]).count()
        return Response({"id": item.pk, "queued": queued})


BROADCAST_FIELDS = ["id", "kind", "title", "text", "photo", "file_id", "url", "from_chat_id", "message_id", "created_by_chat", "cursor"]


class BotBroadcastNextView(BotAPIView):
    """The broadcast to work on: the one already being sent (after a restart), else the oldest queued one."""

    @extend_schema(exclude=True)
    @transaction.atomic
    def get(self, request):
        item = (
            BotBroadcast.objects.select_for_update().filter(status=BotBroadcast.Status.SENDING).order_by("id").first()
            or BotBroadcast.objects.select_for_update().filter(status=BotBroadcast.Status.PENDING).order_by("id").first()
        )
        if item is None:
            return Response({"broadcast": None})
        if item.status == BotBroadcast.Status.PENDING:
            item.status = BotBroadcast.Status.SENDING
            item.started_at = timezone.now()
            item.total = BotSubscriber.objects.filter(is_blocked=False).count()
            item.save(update_fields=["status", "started_at", "total"])
        return Response({"broadcast": {f: getattr(item, f) for f in BROADCAST_FIELDS}})


class BotSubscribersView(BotAPIView):
    """Recipients in id order, a page at a time: [[id, chat_id], ...]."""

    @extend_schema(exclude=True)
    def get(self, request):
        try:
            after = int(request.query_params.get("after", 0))
            limit = max(1, min(int(request.query_params.get("limit", 500)), 1000))
        except ValueError:
            return Response({"detail": "after/limit son bo‘lsin"}, status=status.HTTP_400_BAD_REQUEST)
        rows = BotSubscriber.objects.filter(is_blocked=False, id__gt=after).order_by("id").values_list("id", "chat_id")[:limit]
        return Response({"items": [list(r) for r in rows]})


class BotBroadcastProgressView(BotAPIView):
    """Progress of a running broadcast: counters (deltas), cursor, unreachable chats, the reusable file_id."""

    @extend_schema(exclude=True)
    def post(self, request, pk):
        item = BotBroadcast.objects.filter(pk=pk).first()
        if item is None:
            return Response({"detail": "not_found"}, status=status.HTTP_404_NOT_FOUND)
        d = request.data
        try:
            sent = max(0, int(d.get("sent", 0) or 0))
            failed = max(0, int(d.get("failed", 0) or 0))
            blocked = [int(c) for c in d.get("blocked", [])]
            cursor = int(d["cursor"]) if "cursor" in d else None
        except (TypeError, ValueError):
            return Response({"detail": "noto‘g‘ri ma’lumot"}, status=status.HTTP_400_BAD_REQUEST)
        if blocked:
            BotSubscriber.objects.filter(chat_id__in=blocked).update(is_blocked=True)
        fields = {"sent": F("sent") + sent, "failed": F("failed") + failed}
        if cursor is not None:
            fields["cursor"] = cursor
        if d.get("file_id") and not item.file_id:
            fields["file_id"] = str(d["file_id"])[:255]
        if d.get("done") and item.status == BotBroadcast.Status.SENDING:
            fields["status"] = BotBroadcast.Status.DONE
            fields["finished_at"] = timezone.now()
        BotBroadcast.objects.filter(pk=pk).update(**fields)
        item.refresh_from_db(fields=["status", "sent", "failed", "total"])
        return Response({"status": item.status, "sent": item.sent, "failed": item.failed, "total": item.total})
