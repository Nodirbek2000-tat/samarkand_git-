"""Admin panel → «Telegram bot»: autopost switch, audience numbers, mandatory channels and broadcast history."""

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsSuperuser

from . import broadcast
from .bot_api import ChannelSerializer
from .models import BotBroadcast, BotChannel, BotState

ACTIVE = [BotBroadcast.Status.PENDING, BotBroadcast.Status.SENDING]


def _payload() -> dict:
    state = BotState.get()
    return {
        "bot": {
            "username": state.username,
            "online": state.online,
            "last_seen": state.last_seen_at,
            "autopost": state.autopost,
            "autopost_since": state.autopost_since,
        },
        "stats": broadcast.stats(),
        "channels": ChannelSerializer(BotChannel.objects.all(), many=True).data,
        "broadcasts": [
            {
                "id": b.pk,
                "kind": b.kind,
                "kind_label": b.get_kind_display(),
                "status": b.status,
                "status_label": b.get_status_display(),
                "title": b.title,
                "url": b.url,
                "total": b.total,
                "sent": b.sent,
                "failed": b.failed,
                "created_at": b.created_at,
                "finished_at": b.finished_at,
            }
            for b in BotBroadcast.objects.all()[:20]
        ],
    }


class BotAdminView(APIView):
    permission_classes = [IsSuperuser]

    @extend_schema(responses={200: dict})
    def get(self, request):
        return Response(_payload())

    @extend_schema(responses={200: dict})
    def patch(self, request):
        if "autopost" in request.data:
            state = BotState.get()
            on = bool(request.data["autopost"])
            if on and not state.autopost:
                state.autopost_since = timezone.now()  # only what is published from now on — no flood of old items
            state.autopost = on
            state.save(update_fields=["autopost", "autopost_since"])
        return Response(_payload())


class BotAdminChannelView(APIView):
    permission_classes = [IsSuperuser]

    @extend_schema(responses={200: dict})
    def patch(self, request, pk):
        BotChannel.objects.filter(pk=pk).update(is_active=bool(request.data.get("is_active")))
        return Response(_payload())

    @extend_schema(responses={200: dict})
    def delete(self, request, pk):
        BotChannel.objects.filter(pk=pk).delete()
        return Response(_payload())


class BotAdminBroadcastCancelView(APIView):
    permission_classes = [IsSuperuser]

    @extend_schema(responses={200: dict})
    def post(self, request, pk):
        BotBroadcast.objects.filter(pk=pk, status__in=ACTIVE).update(status=BotBroadcast.Status.CANCELLED, finished_at=timezone.now())
        return Response(_payload())
