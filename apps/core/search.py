"""Site-wide search: every public page type, ready for the header's live search and the /search page."""

import html
import re

from django.db.models import Case, IntegerField, Q, Value, When
from django.utils.html import strip_tags
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.content.models import Announcement, Film, Gallery, News
from apps.core.models import Page
from apps.council.models import BoardMember, CouncilMember, Leader, Meeting
from apps.forum.models import ForumEdition
from apps.partners.models import Partner
from apps.projects.models import Project

# Uzbek apostrophes are typed in many ways (o'zbek, o‘zbek, oʻzbek, o`zbek): any of them finds the others
APOSTROPHES = "'‘’`ʻʼ"
# editable pages (admin → Sahifalar) and the site address each one is shown at
PAGE_URLS = {
    "about": "/about",
    "about-history": "/about/history",
    "about-corporate": "/about/corporate",
    "membership": "/about/membership",
    "meetings": "/council/meetings",
    "recognition": "/council/recognition",
    "cooperation": "/cooperation",
    "projects-active": "/projects/active",
    "projects-completed": "/projects/completed",
}
PER_KIND = 8


def word_pattern(word):
    """A regex for one search word that works the same in PostgreSQL and SQLite (and ignores case in any script)."""
    return "".join(f"[{APOSTROPHES}]" if ch in APOSTROPHES else re.escape(ch) for ch in word)


def plain(value):
    return " ".join(html.unescape(strip_tags(value or "")).split())


def snippet(text, deeper, finder, size=220):
    """The short description — or, when the words only occur deeper in the text, the passage around them."""
    if text and finder.search(text):
        return text[:size]
    for value in deeper:
        match = finder.search(value)
        if match:
            start = max(0, match.start() - 70)
            # start on a word boundary
            if start:
                start = value.find(" ", start) + 1 or start
            part = value[start : start + size].strip()
            return ("…" if start else "") + part + ("…" if start + size < len(value) else "")
    return text[:size]


class SearchView(APIView):
    """Site-wide search across published content."""

    permission_classes = [AllowAny]

    @extend_schema(responses={200: dict})
    def get(self, request):
        q = " ".join((request.query_params.get("q") or "").split())[:100]
        if len(q) < 2:
            return Response({"query": q, "results": []})
        patterns = [word_pattern(w) for w in q.split()[:6]]
        finder = re.compile("|".join(patterns), re.IGNORECASE)
        results = []

        def add(qs, kind, url, fields, title="title", text=lambda o: "", deeper=()):
            """Every word must occur in one of `fields`; objects whose title holds all of them come first."""
            match = Q()
            in_title = Q()
            for p in patterns:
                any_field = Q()
                for f in fields:
                    any_field |= Q(**{f"{f}__iregex": p})
                match &= any_field
                in_title &= Q(**{f"{title}__iregex": p})
            qs = (
                qs.filter(match)
                .annotate(_rank=Case(When(in_title, then=Value(0)), default=Value(1), output_field=IntegerField()))
                .order_by("_rank", *qs.model._meta.ordering)
                .distinct()
            )
            for obj in qs[:PER_KIND]:
                body = [plain(getattr(obj, f, "")) for f in deeper]
                results.append(
                    {
                        "kind": kind,
                        "title": getattr(obj, title),
                        "text": snippet(plain(text(obj)), body, finder),
                        "url": url(obj),
                    }
                )

        add(
            Page.objects.filter(key__in=PAGE_URLS),
            "Sahifa", lambda o: PAGE_URLS[o.key], ["title", "subtitle", "body"],
            text=lambda o: o.subtitle, deeper=["body"],
        )
        add(
            News.objects.filter(is_published=True),
            "Yangilik", lambda o: f"/news/{o.slug}", ["title", "excerpt", "body"],
            text=lambda o: o.excerpt, deeper=["body"],
        )
        add(
            Project.objects.filter(is_published=True),
            "Loyiha", lambda o: f"/projects/{o.slug}", ["title", "summary", "body", "objectives"],
            text=lambda o: o.summary, deeper=["body", "objectives"],
        )
        add(
            Announcement.objects.filter(is_published=True),
            "E’lon", lambda o: f"/announcements/{o.slug}", ["title", "excerpt", "body", "location"],
            text=lambda o: o.excerpt, deeper=["body"],
        )
        add(
            CouncilMember.objects.filter(is_active=True),
            "Kengash a’zosi", lambda o: f"/council/members/{o.slug}", ["full_name", "company", "position", "industry"],
            title="full_name", text=lambda o: ", ".join(filter(None, [o.position, o.company])),
        )
        add(
            BoardMember.objects.filter(is_active=True),
            "Boshqaruv", lambda o: f"/council/management/{o.slug}", ["full_name", "workplace"],
            title="full_name", text=lambda o: o.workplace or o.get_role_display(),
        )
        add(
            Leader.objects.filter(is_active=True),
            "Rahbariyat", lambda o: "/council/leadership", ["full_name", "position", "organization"],
            title="full_name", text=lambda o: o.position,
        )
        add(
            Meeting.objects.filter(is_published=True),
            "Yig‘ilish", lambda o: "/council/meetings", ["title", "host_company", "agenda", "outcome"],
            text=lambda o: o.host_company, deeper=["agenda", "outcome"],
        )
        add(
            ForumEdition.objects.filter(is_published=True),
            "Forum", lambda o: f"/business-environment/forum/{o.year}", ["title", "intro", "nominations__winners__name"],
            text=lambda o: o.dates, deeper=["intro"],
        )
        add(
            Film.objects.filter(is_published=True),
            "Film", lambda o: f"/news/films/{o.slug}", ["title", "company", "owner_name", "description"],
            text=lambda o: o.company, deeper=["description"],
        )
        add(
            Gallery.objects.filter(is_published=True),
            "Fotohisobot", lambda o: f"/gallery/{o.slug}", ["title", "description", "location"],
            text=lambda o: o.description,
        )
        add(
            Partner.objects.filter(is_published=True),
            "Hamkor", lambda o: "/cooperation", ["name", "description", "country"],
            title="name", text=lambda o: o.description or o.country,
        )
        return Response({"query": q, "results": results})
