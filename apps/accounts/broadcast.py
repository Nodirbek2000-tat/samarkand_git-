"""
Bot audience and broadcasts.

* `stats()` — numbers for the bot's /admin and the admin panel.
* `is_bot_admin()` — who may open the bot's /admin: administrators of the site (superusers) who signed up through the bot.
* Autopost: when an item is published on the site (news, announcement, project/startup, film, photo report, forum)
  and «botga yuborish» is on, one `BotBroadcast` is queued for it — once per object, never again on later edits.
  People (council members, board, leaders) are never posted.
"""

import html
import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models.signals import post_save
from django.utils import timezone
from django.utils.html import strip_tags

from .models import BotBroadcast, BotChannel, BotState, BotSubscriber, TelegramAccount

User = get_user_model()

CAPTION_TEXT = 620  # Telegram allows 1024 characters in a photo caption; leave room for the title and prefix


def stats() -> dict:
    now = timezone.now()
    today = timezone.localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)
    subs = BotSubscriber.objects
    last = BotBroadcast.objects.exclude(status=BotBroadcast.Status.PENDING).first()
    return {
        "subscribers": {
            "total": subs.count(),
            "active": subs.filter(is_blocked=False).count(),
            "blocked": subs.filter(is_blocked=True).count(),
            "today": subs.filter(joined_at__gte=today).count(),
            "week": subs.filter(joined_at__gte=now - timedelta(days=7)).count(),
        },
        "site": {
            "users": User.objects.filter(is_active=True).count(),
            "registered": TelegramAccount.objects.count(),
            "staff": User.objects.filter(is_active=True, is_staff=True).count(),
        },
        "channels": BotChannel.objects.filter(is_active=True).count(),
        "queue": BotBroadcast.objects.filter(status__in=[BotBroadcast.Status.PENDING, BotBroadcast.Status.SENDING]).count(),
        "last": last
        and {"title": last.title, "kind": last.kind, "status": last.status, "sent": last.sent, "failed": last.failed, "total": last.total},
    }


def is_bot_admin(telegram_id: int) -> bool:
    return TelegramAccount.objects.filter(
        telegram_id=telegram_id, user__is_active=True, user__is_staff=True, user__is_superuser=True
    ).exists()


# ---------------------------------------------------------------------------------------------- autopost


def _text(value: str) -> str:
    text = re.sub(r"\s+", " ", strip_tags(value or "")).strip()
    text = html.unescape(text)
    if len(text) > CAPTION_TEXT:
        text = text[:CAPTION_TEXT].rsplit(" ", 1)[0].rstrip(".,;:—- ") + "…"
    return text


def _project_label(obj) -> str:
    return {"startup": "🚀 Yoshlar startapi", "club": "🤝 Biznes klub", "science": "🔬 Ilmiy ishlanma"}.get(obj.category, "📌 Loyiha")


# model label → (heading, site path, text field)
SOURCES = {
    "content.news": (lambda o: "📰 Yangilik", lambda o: f"/news/{o.slug}", "excerpt"),
    "content.announcement": (lambda o: "📣 E’lon", lambda o: f"/announcements/{o.slug}", "excerpt"),
    "content.film": (lambda o: "🎬 Film", lambda o: f"/news/films/{o.slug}", "description"),
    "content.gallery": (lambda o: "📸 Fotohisobot", lambda o: f"/gallery/{o.slug}", "description"),
    "projects.project": (_project_label, lambda o: f"/projects/{o.slug}", "summary"),
    "forum.forumedition": (lambda o: "🏭 Sanoatchilar forumi", lambda o: f"/business-environment/forum/{o.year}", "intro"),
}


def announce(obj) -> BotBroadcast | None:
    """Queue `obj` for every subscriber (once). Returns the broadcast, or None if it was announced before."""
    heading, path, field = SOURCES[obj._meta.label_lower]
    body = _text(getattr(obj, field, "") or "")
    title = getattr(obj, "title", "") or str(obj)
    text = f"{heading}\n\n<b>{html.escape(title, quote=False)}</b>"
    if body:
        text += f"\n\n{html.escape(body, quote=False)}"
    cover = getattr(obj, "cover", None)
    try:
        with transaction.atomic():
            return BotBroadcast.objects.create(
                kind=BotBroadcast.Kind.POST,
                source=f"{obj._meta.label_lower}:{obj.pk}",
                title=title[:255],
                text=text,
                photo=cover.url if cover else "",
                url=path(obj),
            )
    except IntegrityError:  # announced already
        return None


def _on_save(sender, instance, **kwargs):
    if not getattr(instance, "is_published", False) or kwargs.get("raw"):
        return
    state = BotState.get()
    published = instance.published_at or timezone.now()
    if not state.autopost or published > timezone.now() or (state.autopost_since and published < state.autopost_since):
        return
    transaction.on_commit(lambda: announce(instance))


def connect():
    from django.apps import apps

    for label in SOURCES:
        post_save.connect(_on_save, sender=apps.get_model(label), dispatch_uid=f"bot-autopost-{label}")
