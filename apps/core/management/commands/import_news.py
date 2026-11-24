"""
Puts news items (with their photos, video and a photo report) on the site from seed/news — idempotent.

    python manage.py import_news            # every folder in apps/core/seed/news
    python manage.py import_news --replace  # rewrite items that are already there
    python manage.py import_news some-slug --replace  # just this one

Each folder is one item; its name is the link (slug). item.json holds:
    title, category (council|projects|forum|business|cooperation|events|other), excerpt, body (HTML),
    published_at (optional, "2025-07-15"), source_url (optional), cover ("1.jpg"), images (["2.jpg", ...]), video_url (optional),
    video_file (optional, "video.mp4"), gallery (optional: {"location", "images": [...]}) — the same event
    then also appears among the photo reports.
Photos are scaled down to 1600 px and stored as WebP.
"""

import json
from datetime import datetime
from io import BytesIO
from pathlib import Path

from django.core.files import File
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageOps

from apps.content.models import Gallery, GalleryImage, News, NewsImage

ROOT = Path(__file__).resolve().parents[2] / "seed" / "news"


def webp(path: Path) -> ContentFile:
    with Image.open(path) as src:
        im = ImageOps.exif_transpose(src).convert("RGB")
    im.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    out = BytesIO()
    im.save(out, "WEBP", quality=84, method=6)
    return ContentFile(out.getvalue(), name=f"{path.stem}.webp")


class Command(BaseCommand):
    help = "Yangiliklarni (rasmlari, videosi va fotohisoboti bilan) seed/news papkasidan joylaydi."

    def add_arguments(self, parser):
        parser.add_argument("slugs", nargs="*", help="faqat shu yangiliklar (papka nomlari)")
        parser.add_argument("--replace", action="store_true", help="bor yangiliklarni ham qayta yozish")

    def handle(self, slugs, replace, **options):
        folders = sorted(p for p in ROOT.iterdir() if (p / "item.json").is_file()) if ROOT.is_dir() else []
        if slugs:
            folders = [p for p in folders if p.name in slugs]
        for folder in folders:
            with transaction.atomic():
                self.one(folder, replace)

    def one(self, folder: Path, replace: bool):
        slug = folder.name
        data = json.loads((folder / "item.json").read_text(encoding="utf-8"))
        news = News.objects.filter(slug=slug).first()
        if news and not replace:
            self.stdout.write(f"– {slug} — bor, o‘tkazib yuborildi (--replace)")
            return
        news = news or News(slug=slug)
        news.title = data["title"]
        news.category = data.get("category", News.Category.COUNCIL)
        news.excerpt = data.get("excerpt", "")
        news.body = data.get("body", "")
        news.video_url = data.get("video_url", "")
        news.source_url = data.get("source_url", "")
        news.is_published = True
        if data.get("published_at"):
            news.published_at = timezone.make_aware(datetime.fromisoformat(data["published_at"]))
        if data.get("cover"):
            news.cover.save("cover.webp", webp(folder / data["cover"]), save=False)
        if data.get("video_file"):
            with open(folder / data["video_file"], "rb") as f:
                news.video_file.save(data["video_file"], File(f), save=False)
        news.save()
        news.images.all().delete()
        for i, name in enumerate(data.get("images", [])):
            NewsImage.objects.create(news=news, image=webp(folder / name), order=i)

        if g := data.get("gallery"):
            gallery = Gallery.objects.filter(slug=slug).first() or Gallery(slug=slug)
            gallery.title = data["title"]
            gallery.description = data.get("excerpt", "")
            gallery.location = g.get("location", "")
            gallery.event_date = (news.published_at or timezone.now()).date()
            gallery.is_published = True
            names = g.get("images") or [data.get("cover"), *data.get("images", [])]
            gallery.cover.save("cover.webp", webp(folder / names[0]), save=False)
            gallery.save()
            gallery.images.all().delete()
            for i, name in enumerate(names):
                GalleryImage.objects.create(gallery=gallery, image=webp(folder / name), order=i)
        self.stdout.write(self.style.SUCCESS(f"✓ {news.title}"))
