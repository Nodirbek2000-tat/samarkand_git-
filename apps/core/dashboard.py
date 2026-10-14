from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.content.models import Announcement, Film, Gallery, News
from apps.council.models import BoardMember, CouncilMember, Leader, Meeting
from apps.core.models import Page
from apps.core.permissions import IsStaff
from apps.forum.models import ForumEdition
from apps.inbox.models import Appeal, CooperationRequest, MemberApplication
from apps.partners.models import Partner
from apps.projects.models import Project


class DashboardView(APIView):
    permission_classes = [IsStaff]

    @extend_schema(responses={200: dict})
    def get(self, request):
        content = {
            "news": (News, "Yangiliklar", "/admin/news"),
            "projects": (Project, "Loyihalar", "/admin/projects"),
            "announcements": (Announcement, "E’lonlar", "/admin/announcements"),
            "galleries": (Gallery, "Fotohisobotlar", "/admin/galleries"),
            "films": (Film, "Filmlar", "/admin/films"),
            "forum": (ForumEdition, "Forumlar", "/admin/forum"),
            "meetings": (Meeting, "Yig‘ilishlar", "/admin/meetings"),
            "pages": (Page, "Sahifalar", "/admin/pages"),
        }
        cards = []
        for key, (model, label, href) in content.items():
            # one query per model instead of two
            counts = model.objects.aggregate(total=Count("pk"), published=Count("pk", filter=Q(is_published=True)))
            cards.append({"key": key, "label": label, "href": href, **counts})

        people = [
            {"key": "council", "label": "Kengash a’zolari", "href": "/admin/council-members", "total": CouncilMember.objects.count()},
            {"key": "board", "label": "Boshqaruv", "href": "/admin/board", "total": BoardMember.objects.count()},
            {"key": "leaders", "label": "Rahbariyat", "href": "/admin/leaders", "total": Leader.objects.count()},
            {"key": "partners", "label": "Hamkorlar", "href": "/admin/partners", "total": Partner.objects.count()},
        ]

        data = {"content": cards, "people": people, "inbox": None, "recent": []}

        if request.user.is_superuser:
            inbox = []
            for key, model, label in (
                ("appeals", Appeal, "Murojaatlar"),
                ("cooperation", CooperationRequest, "Hamkorlik takliflari"),
                ("applications", MemberApplication, "A’zolik arizalari"),
            ):
                inbox.append(
                    {
                        "key": key,
                        "label": label,
                        "total": model.objects.count(),
                        "new": model.objects.filter(status="new").count(),
                    }
                )
            since = timezone.now() - timedelta(days=29)
            series = {}
            for model in (Appeal, CooperationRequest, MemberApplication):
                rows = (
                    model.objects.filter(created_at__gte=since)
                    .annotate(day=TruncDate("created_at"))
                    .values_list("day", flat=True)
                )
                for day in rows:
                    series[day.isoformat()] = series.get(day.isoformat(), 0) + 1
            days = [(since + timedelta(days=i)).date().isoformat() for i in range(30)]
            data["inbox"] = {"groups": inbox, "daily": [{"date": d, "count": series.get(d, 0)} for d in days]}
            from apps.accounts.models import BotMessage, BotState, TelegramAccount

            week = timezone.now() - timedelta(days=7)
            data["site_users"] = {
                "total": TelegramAccount.objects.count(),
                "week": TelegramAccount.objects.filter(created_at__gte=week).count(),
            }
            bot = BotState.get()
            data["bot"] = {
                "username": bot.username,
                "online": bot.online,
                "last_seen": bot.last_seen_at,
                "pending": BotMessage.objects.filter(status=BotMessage.Status.PENDING).count(),
                "failed": BotMessage.objects.filter(status=BotMessage.Status.FAILED, created_at__gte=week).count(),
            }

        recent = []
        for model, kind, href in (
            (News, "Yangilik", "/admin/news"),
            (Project, "Loyiha", "/admin/projects"),
            (Announcement, "E’lon", "/admin/announcements"),
            (Gallery, "Fotohisobot", "/admin/galleries"),
        ):
            for obj in model.objects.order_by("-updated_at")[:5]:
                recent.append(
                    {
                        "kind": kind,
                        "title": obj.title,
                        "href": f"{href}/{obj.pk}",
                        "updated_at": obj.updated_at,
                        "is_published": obj.is_published,
                    }
                )
        data["recent"] = sorted(recent, key=lambda r: r["updated_at"], reverse=True)[:8]
        return Response(data)


class SearchView(APIView):
    """Site-wide search across published content."""

    permission_classes = [AllowAny]

    @extend_schema(responses={200: dict})
    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        if len(q) < 2:
            return Response({"query": q, "results": []})
        results = []

        def add(qs, kind, url, title_attr="title", text_attr=None, limit=8):
            for obj in qs[:limit]:
                text = getattr(obj, text_attr, "") if text_attr else ""
                results.append({"kind": kind, "title": getattr(obj, title_attr), "text": (text or "")[:220], "url": url(obj)})

        add(
            News.objects.filter(is_published=True).filter(Q(title__icontains=q) | Q(excerpt__icontains=q) | Q(body__icontains=q)),
            "Yangilik", lambda o: f"/news/{o.slug}", text_attr="excerpt",
        )
        add(
            Project.objects.filter(is_published=True).filter(Q(title__icontains=q) | Q(summary__icontains=q) | Q(body__icontains=q)),
            "Loyiha", lambda o: f"/projects/{o.slug}", text_attr="summary",
        )
        add(
            Announcement.objects.filter(is_published=True).filter(Q(title__icontains=q) | Q(excerpt__icontains=q)),
            "E’lon", lambda o: f"/announcements/{o.slug}", text_attr="excerpt",
        )
        add(
            CouncilMember.objects.filter(is_active=True).filter(Q(full_name__icontains=q) | Q(company__icontains=q)),
            "Kengash a’zosi", lambda o: f"/council/members/{o.slug}", title_attr="full_name", text_attr="company",
        )
        add(
            Gallery.objects.filter(is_published=True).filter(title__icontains=q),
            "Fotohisobot", lambda o: f"/gallery/{o.slug}", text_attr="description",
        )
        add(
            ForumEdition.objects.filter(is_published=True)
            .filter(Q(title__icontains=q) | Q(nominations__winners__name__icontains=q))
            .distinct(),
            "Forum", lambda o: f"/business-environment/forum/{o.year}", text_attr="dates",
        )
        return Response({"query": q, "results": results})
