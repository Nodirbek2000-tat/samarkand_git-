import uuid
from pathlib import Path

from django.db import models
from django.utils import timezone

from .text import clean_html, unique_slug
from .validators import image_validators


class _UploadTo:
    """Store uploads under <folder>/<yyyy>/<mm>/<uuid>.<ext> — no user-controlled names on disk."""

    def __init__(self, folder: str):
        self.folder = folder

    def __call__(self, instance, filename: str) -> str:
        ext = Path(filename).suffix.lower()[:10]
        now = timezone.now()
        return f"{self.folder}/{now:%Y/%m}/{uuid.uuid4().hex}{ext}"

    def deconstruct(self):
        return ("apps.core.models._UploadTo", (self.folder,), {})


covers_upload = _UploadTo("covers")
gallery_upload = _UploadTo("gallery")
people_upload = _UploadTo("people")
logos_upload = _UploadTo("logos")
documents_upload = _UploadTo("documents")
editor_upload = _UploadTo("editor")
videos_upload = _UploadTo("videos")


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("Yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan", auto_now=True)

    class Meta:
        abstract = True


class OrderedModel(models.Model):
    order = models.PositiveIntegerField("Tartib", default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ["order", "id"]


class PublishableModel(models.Model):
    is_published = models.BooleanField("E’lon qilingan", default=False, db_index=True)
    published_at = models.DateTimeField("E’lon qilingan sana", null=True, blank=True, db_index=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class SluggedModel(models.Model):
    """Fills `slug` from `title` once; slugs stay stable afterwards so links never break."""

    slug = models.SlugField("Havola (slug)", max_length=90, unique=True, blank=True)
    SLUG_SOURCE = "title"

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, getattr(self, self.SLUG_SOURCE) or "")
        super().save(*args, **kwargs)


class RichTextMixin:
    """Sanitises every field listed in RICH_TEXT_FIELDS before saving."""

    RICH_TEXT_FIELDS: tuple[str, ...] = ()

    def save(self, *args, **kwargs):
        for name in self.RICH_TEXT_FIELDS:
            setattr(self, name, clean_html(getattr(self, name)))
        super().save(*args, **kwargs)


class SiteSettings(TimeStampedModel):
    """Singleton with contacts, socials and headline numbers shown across the site."""

    org_name = models.CharField(
        "Tashkilot nomi", max_length=255, default="«Yangi Samarqand» tadbirkorlar jamoat fondi"
    )
    council_name = models.CharField(
        "Kengash nomi", max_length=255, default="Samarqand viloyati tadbirkorlarining jamoat maslahat kengashi"
    )
    slogan = models.CharField("Shior", max_length=255, blank=True)
    phone = models.CharField("Telefon", max_length=40, blank=True)
    phone_secondary = models.CharField("Qo‘shimcha telefon", max_length=40, blank=True)
    email = models.EmailField("Email", blank=True)
    address = models.CharField("Manzil", max_length=255, blank=True)
    working_hours = models.CharField("Ish vaqti", max_length=120, blank=True)
    map_embed_url = models.URLField("Xarita (embed havola)", max_length=600, blank=True)
    telegram = models.URLField("Telegram", blank=True)
    instagram = models.URLField("Instagram", blank=True)
    facebook = models.URLField("Facebook", blank=True)
    youtube = models.URLField("YouTube", blank=True)
    catalog_url = models.URLField("Made in Samarkand katalog havolasi", blank=True)

    stat_members = models.PositiveIntegerField("Kengash a’zolari soni", default=0)
    stat_catalog = models.PositiveIntegerField("Katalogdagi korxonalar", default=0)
    stat_startups = models.PositiveIntegerField("Qo‘llab-quvvatlangan startaplar", default=0)
    stat_enterprises = models.PositiveIntegerField("Viloyatdagi sanoat korxonalari", default=0)

    CACHE_TAGS = ("settings",)

    class Meta:
        verbose_name = "Sayt sozlamalari"
        verbose_name_plural = "Sayt sozlamalari"

    def __str__(self):
        return "Sayt sozlamalari"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SiteSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Page(RichTextMixin, TimeStampedModel, PublishableModel):
    """
    Editable content pages (about, history, membership terms, council meetings, clubs...).
    The frontend looks pages up by a fixed `key`, so admins edit the text without touching code.
    """

    class Section(models.TextChoices):
        ABOUT = "about", "Biz haqimizda"
        COUNCIL = "council", "Kengash"
        PROJECTS = "projects", "Loyihalar"
        BUSINESS = "business", "Biznes muhit"
        COOPERATION = "cooperation", "Hamkorlik"
        OTHER = "other", "Boshqa"

    key = models.SlugField("Kalit", max_length=80, unique=True, help_text="Sahifa manzili bilan bog‘langan kalit")
    section = models.CharField(
        "Bo‘lim", max_length=20, choices=Section.choices, default=Section.OTHER, db_index=True
    )
    title = models.CharField("Sarlavha", max_length=255)
    subtitle = models.CharField("Qisqa tavsif", max_length=500, blank=True)
    body = models.TextField("Matn", blank=True)
    blocks = models.JSONField(
        "Kartochkalar",
        default=list,
        blank=True,
        help_text='Tuzilgan bloklar: [{"group": "values", "title": "...", "body": "..."}]',
    )
    cover = models.ImageField("Muqova", upload_to=covers_upload, blank=True, validators=image_validators)
    seo_description = models.CharField("SEO tavsif", max_length=300, blank=True)

    RICH_TEXT_FIELDS = ("body",)
    CACHE_TAGS = ("pages",)

    class Meta:
        verbose_name = "Sahifa"
        verbose_name_plural = "Sahifalar"
        ordering = ["section", "title"]

    def __str__(self):
        return self.title


class EditorUpload(TimeStampedModel):
    """Images inserted inline through the rich-text editor."""

    file = models.ImageField("Rasm", upload_to=editor_upload, validators=image_validators)

    class Meta:
        verbose_name = "Matn ichidagi rasm"
        verbose_name_plural = "Matn ichidagi rasmlar"
