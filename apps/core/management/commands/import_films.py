"""
Puts films (Uz Made and other company videos) on the site from seed/films — idempotent.

    python manage.py import_films             # every folder in apps/core/seed/films
    python manage.py import_films slug --replace

Each folder is one film; its name is the link (slug). item.json holds:
    title, company, owner_name (optional), description (HTML), video_url (YouTube) or video_file ("video.mp4"),
    cover ("cover.jpg", optional), duration (optional, "12:40"), order (optional), published_at (optional).
"""

import json
from datetime import datetime
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.content.models import Film

from .import_news import webp

ROOT = Path(__file__).resolve().parents[2] / "seed" / "films"


class Command(BaseCommand):
    help = "Filmlarni seed/films papkasidan joylaydi."

    def add_arguments(self, parser):
        parser.add_argument("slugs", nargs="*")
        parser.add_argument("--replace", action="store_true")

    def handle(self, slugs, replace, **options):
        folders = sorted(p for p in ROOT.iterdir() if (p / "item.json").is_file()) if ROOT.is_dir() else []
        for folder in folders:
            if slugs and folder.name not in slugs:
                continue
            data = json.loads((folder / "item.json").read_text(encoding="utf-8"))
            film = Film.objects.filter(slug=folder.name).first()
            if film and not replace:
                self.stdout.write(f"– {folder.name} — bor, o‘tkazib yuborildi (--replace)")
                continue
            film = film or Film(slug=folder.name)
            for key in ("title", "company", "owner_name", "description", "video_url", "duration"):
                setattr(film, key, data.get(key, ""))
            film.order = data.get("order", 0)
            film.is_published = True
            if data.get("published_at"):
                film.published_at = timezone.make_aware(datetime.fromisoformat(data["published_at"]))
            if data.get("cover"):
                film.cover.save("cover.webp", webp(folder / data["cover"]), save=False)
            if data.get("video_file"):
                with open(folder / data["video_file"], "rb") as f:
                    film.video_file.save(data["video_file"], File(f), save=False)
            film.save()
            self.stdout.write(self.style.SUCCESS(f"✓ {film.title}"))
