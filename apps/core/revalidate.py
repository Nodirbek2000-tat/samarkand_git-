"""
Keeps the Next.js cache in sync with the database.

Any model that declares `CACHE_TAGS = ("news", ...)` queues its tags after the surrounding
transaction commits. Tags are debounced for a moment, so a bulk save (e.g. a whole forum
structure) sends a single request to the frontend.
"""

import json
import logging
import threading
import urllib.request

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_pending: set[str] = set()
_timer: threading.Timer | None = None
DEBOUNCE_SECONDS = 0.4


def _post(tags: list[str]) -> None:
    body = json.dumps({"tags": tags}).encode()
    req = urllib.request.Request(
        settings.NEXT_REVALIDATE_URL,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "X-Revalidate-Secret": settings.NEXT_REVALIDATE_SECRET},
    )
    try:
        urllib.request.urlopen(req, timeout=4).close()
    except Exception as exc:  # the frontend may simply be offline in development
        logger.info("Frontend revalidation skipped (%s): %s", ", ".join(tags), exc)


def _flush() -> None:
    global _timer
    with _lock:
        tags = sorted(_pending)
        _pending.clear()
        _timer = None
    if tags:
        _post(tags)


def _queue(tags) -> None:
    global _timer
    with _lock:
        _pending.update(tags)
        if _timer is None:
            _timer = threading.Timer(DEBOUNCE_SECONDS, _flush)
            _timer.daemon = True
            _timer.start()


def notify_frontend(tags) -> None:
    tags = set(tags)
    if tags:
        transaction.on_commit(lambda: _queue(tags))


def _handler(sender, instance, **kwargs):
    tags = getattr(sender, "CACHE_TAGS", None)
    if tags and not kwargs.get("raw"):
        notify_frontend(tags)


def connect_signals() -> None:
    post_save.connect(_handler, dispatch_uid="next_revalidate_save")
    post_delete.connect(_handler, dispatch_uid="next_revalidate_delete")
