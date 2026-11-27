"""
Loads a bundle made by build_catalog_bundle into the catalog — idempotent (rows are matched by their id in the
former madeinsam.uz database):

    python manage.py import_catalog /path/to/bundle            # new rows only; existing ones keep admin edits
    python manage.py import_catalog /path/to/bundle --replace  # rewrite texts and pictures from the bundle
"""

import json
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Category, Company, CompanyImage, Product, ProductImage
from apps.core.text import unique_slug

COMPANY_FIELDS = (
    "title", "description", "address", "phone", "sales_manager", "email", "website", "telegram", "instagram",
    "facebook", "youtube", "whatsapp",
)


class Command(BaseCommand):
    help = "build_catalog_bundle yasagan to‘plamni «Made in Samarkand» katalogiga yuklaydi."

    def add_arguments(self, parser):
        parser.add_argument("bundle")
        parser.add_argument("--replace", action="store_true", help="bor yozuvlarni ham to‘plamdagidek qayta yozish")

    def handle(self, bundle, replace, **options):
        self.root = Path(bundle)
        data_file = self.root / "data.json"
        if not data_file.is_file():
            raise CommandError(f"data.json topilmadi: {data_file}")
        data = json.loads(data_file.read_text(encoding="utf-8"))
        self.replace = replace
        with transaction.atomic():
            categories = {row["id"]: self.category(i, row) for i, row in enumerate(data["categories"])}
            companies = {row["id"]: self.company(row, categories) for row in data["companies"]}
            products = [self.product(row, companies, categories) for row in data["products"]]
        made = sum(1 for p in products if p)
        self.stdout.write(self.style.SUCCESS(
            f"Kategoriya: {len(categories)}, korxona: {len(companies)}, mahsulot: {made} (yangi yoki yangilangan)."
        ))

    def attach(self, field, name: str) -> None:
        if name:
            with (self.root / "img" / name).open("rb") as f:
                field.save(name, File(f), save=False)

    def category(self, order: int, row: dict) -> Category:
        obj, created = Category.objects.get_or_create(source_id=row["id"], defaults={"title": row["title"], "order": order})
        if created or self.replace:
            obj.title, obj.order = row["title"], order
            if created:  # «Avtomobilsozlik mahsulotlari, …» → /avtomobilsozlik-mahsulotlari, not the whole sentence
                obj.slug = unique_slug(obj, row["title"].split(",")[0])
            if not obj.image or self.replace:
                self.attach(obj.image, row["image"])
            obj.save()
        return obj

    def company(self, row: dict, categories: dict) -> Company:
        obj = Company.objects.filter(source_id=row["id"]).first()
        if obj and not self.replace:
            return obj
        obj = obj or Company(source_id=row["id"])
        for key in COMPANY_FIELDS:
            setattr(obj, key, row[key])
        obj.category = categories[row["category"]]
        if not obj.logo or self.replace:
            self.attach(obj.logo, row["logo"])
        obj.save()
        if self.replace or not obj.images.exists():
            obj.images.all().delete()
            for i, name in enumerate(row["images"]):
                image = CompanyImage(company=obj, order=i)
                self.attach(image.image, name)
                image.save()
        return obj

    def product(self, row: dict, companies: dict, categories: dict) -> Product | None:
        obj = Product.objects.filter(source_id=row["id"]).first()
        if obj and not self.replace:
            return None
        obj = obj or Product(source_id=row["id"])
        obj.company, obj.category = companies[row["company"]], categories[row["category"]]
        obj.name, obj.description = row["name"], row["description"]
        obj.save()
        obj.images.all().delete()
        for i, name in enumerate(row["images"]):
            image = ProductImage(product=obj, order=i)
            self.attach(image.image, name)
            image.save()
        return obj
