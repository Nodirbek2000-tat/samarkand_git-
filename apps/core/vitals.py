"""
Real-user speed measurements: every visitor's browser reports how the page behaved on that device
(load, freezes, scroll smoothness, the heaviest code), and the admin panel shows the summary — so speed work
is based on real phones and computers, not guesses. No personal data is kept (no IP, no account).
"""

import random
from collections import defaultdict
from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import PerfSample
from .permissions import IsSuperuser

KEEP_DAYS = 30
DEVICE_LABELS = {"phone": "Telefon", "tablet": "Planshet", "desktop": "Kompyuter"}


class PerfSampleSerializer(serializers.ModelSerializer):
    page = serializers.CharField(max_length=200)
    device = serializers.ChoiceField(choices=list(DEVICE_LABELS))
    globe = serializers.ChoiceField(choices=["", "3d", "poster", "slow"], required=False, allow_blank=True)
    # a broken or hostile report must not store nonsense
    lcp_ms = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=600_000)
    ready_ms = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=600_000)
    inp_ms = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=60_000)
    cls = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=100)
    tbt_ms = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=600_000)
    longest_ms = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=600_000)
    frames = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=1_000_000)
    janky = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=1_000_000)
    worst_frame_ms = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=600_000)
    cores = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=1024)
    memory = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=1024)
    width = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=20_000)

    class Meta:
        model = PerfSample
        exclude = ["id", "created_at"]
        extra_kwargs = {
            "browser": {"max_length": 40},
            "net": {"max_length": 10},
            "culprit": {"max_length": 200},
        }

    def to_internal_value(self, data):
        # trim long free-text values instead of rejecting the whole report
        if isinstance(data, dict):
            data = {**data}
            for key, size in (("page", 200), ("browser", 40), ("net", 10), ("culprit", 200)):
                if isinstance(data.get(key), str):
                    data[key] = data[key][:size]
        return super().to_internal_value(data)


class VitalsView(APIView):
    """The site's own beacon (navigator.sendBeacon) — anonymous, no session, rate-limited per address."""

    permission_classes = [AllowAny]
    authentication_classes = []  # no session → no CSRF check for this anonymous, write-only endpoint
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "vitals"

    @extend_schema(request=PerfSampleSerializer, responses={204: None})
    def post(self, request):
        serializer = PerfSampleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # now and then: forget measurements older than a month
        if random.random() < 0.01:
            PerfSample.objects.filter(created_at__lt=timezone.now() - timedelta(days=KEEP_DAYS)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def p75(values):
    """75th percentile (nearest rank) — the number Google uses for Core Web Vitals; None when there is no data."""
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    return values[min(len(values) - 1, int(len(values) * 0.75))]


def jank_pct(rows):
    frames = sum(r["frames"] or 0 for r in rows)
    janky = sum(r["janky"] or 0 for r in rows)
    return round(janky * 100 / frames, 1) if frames else None


def summarize(rows):
    return {
        "samples": len(rows),
        "lcp_p75": p75(r["lcp_ms"] for r in rows),
        "ready_p75": p75(r["ready_ms"] for r in rows),
        "tbt_p75": p75(r["tbt_ms"] for r in rows),
        "longest_p75": p75(r["longest_ms"] for r in rows),
        "inp_p75": p75(r["inp_ms"] for r in rows),
        "cls_p75": p75(r["cls"] for r in rows),
        "jank_pct": jank_pct(rows),
    }


class VitalsReportView(APIView):
    """Summary for the admin panel (administrators only)."""

    permission_classes = [IsSuperuser]

    @extend_schema(responses={200: dict})
    def get(self, request):
        try:
            days = max(1, min(KEEP_DAYS, int(request.query_params.get("days", 7))))
        except ValueError:
            days = 7
        since = timezone.now() - timedelta(days=days)
        fields = [
            "created_at", "page", "device", "browser", "lite", "cores", "memory", "net", "width", "lcp_ms", "ready_ms",
            "inp_ms", "cls", "tbt_ms", "longest_ms", "frames", "janky", "worst_frame_ms", "culprit", "globe",
        ]
        rows = list(PerfSample.objects.filter(created_at__gte=since).values(*fields)[:20000])

        groups = defaultdict(list)
        pages = defaultdict(list)
        browsers = defaultdict(int)
        culprits = defaultdict(list)
        globe = defaultdict(int)
        for r in rows:
            groups[(r["device"], r["lite"])].append(r)
            pages[r["page"]].append(r)
            browsers[r["browser"] or "—"] += 1
            if r["culprit"]:
                culprits[r["culprit"]].append(r)
            if r["globe"]:
                globe[r["globe"]] += 1

        order = {"phone": 0, "tablet": 1, "desktop": 2}
        return Response(
            {
                "days": days,
                "summary": {**summarize(rows), "lite_pct": round(sum(r["lite"] for r in rows) * 100 / len(rows), 1) if rows else None},
                "globe": dict(globe),
                "groups": [
                    {"device": d, "label": DEVICE_LABELS.get(d, d), "lite": lite, **summarize(g)}
                    for (d, lite), g in sorted(groups.items(), key=lambda kv: (order.get(kv[0][0], 9), kv[0][1]))
                ],
                "pages": sorted(
                    ({"page": p, **summarize(g)} for p, g in pages.items()), key=lambda x: -x["samples"]
                )[:15],
                "browsers": sorted(({"browser": b, "samples": n} for b, n in browsers.items()), key=lambda x: -x["samples"])[:8],
                "culprits": sorted(
                    ({"culprit": c, "samples": len(g), "longest_p75": p75(r["longest_ms"] for r in g)} for c, g in culprits.items()),
                    key=lambda x: -x["samples"],
                )[:10],
                "worst": sorted((r for r in rows if r["tbt_ms"] is not None), key=lambda r: -r["tbt_ms"])[:15],
            }
        )
