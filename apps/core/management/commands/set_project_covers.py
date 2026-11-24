"""
Gives projects their cover from seed/project_covers/<slug>.(jpg|png|webp) — idempotent.

    python manage.py set_project_covers            # only projects without a cover
    python manage.py set_project_covers --replace  # also replace existing covers
"""

from pathlib import Path

from django.core.management.base import BaseCommand

from apps.projects.models import Project

from .import_news import webp

ROOT = Path(__file__).resolve().parents[2] / "seed" / "project_covers"


class Command(BaseCommand):
    help = "Loyihalarga muqova rasmini seed/project_covers papkasidan qo‘yadi."

    def add_arguments(self, parser):
        parser.add_argument("--replace", action="store_true")

    def handle(self, replace, **options):
        for path in sorted(ROOT.glob("*")) if ROOT.is_dir() else []:
            if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            project = Project.objects.filter(slug=path.stem).first()
            if not project:
                self.stderr.write(f"✗ {path.name}: loyiha topilmadi")
                continue
            if project.cover and not replace:
                self.stdout.write(f"– {project.title} — muqova bor (--replace)")
                continue
            project.cover.save("cover.webp", webp(path), save=False)
            project.save(update_fields=["cover"])
            self.stdout.write(self.style.SUCCESS(f"✓ {project.title}"))
