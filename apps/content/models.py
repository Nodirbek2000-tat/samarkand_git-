from django.db import models

from apps.core.models import (
    OrderedModel,
    PublishableModel,
    RichTextMixin,
    SluggedModel,
    TimeStampedModel,
    covers_upload,
    videos_upload,
    gallery_upload,
)
from apps.core.validators import image_validators, video_validators


class News(RichTextMixin, SluggedModel, PublishableModel, TimeStampedModel):
    class Category(models.TextChoices):
        COUNCIL = "council", "Kengash"
        PROJECTS = "projects", "Loyihalar"
        FORUM = "forum", "Forum"
        BUSINESS = "business", "Biznes"
        COOPERATION = "cooperation", "Hamkorlik"
        EVENTS = "events", "Tadbirlar"
        OTHER = "other", "Boshqa"

    title = models.CharField("Sarlavha", max_length=255)
    category = models.CharField("Turkum", max_length=20, choices=Category.choices, default=Category.COUNCIL, db_index=True)
    excerpt = models.TextField("Qisqa mazmun", max_length=600, blank=True)
    body = models.TextField("Matn", blank=True)
    cover = models.ImageField("Muqova rasmi", upload_to=covers_upload, blank=True, validators=image_validators)
    source_url = models.URLField("Manba havolasi", blank=True)
    is_featured = models.BooleanField("Asosiy yangilik", default=False)
    views = models.PositiveIntegerField("Ko‘rishlar", default=0, editable=False)

    RICH_TEXT_FIELDS = ("body",)
    CACHE_TAGS = ("news",)

    class Meta:
        verbose_name = "Yangilik"
        verbose_name_plural = "Yangiliklar"
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title


class NewsImage(OrderedModel):
    news = models.ForeignKey(News, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField("Rasm", upload_to=gallery_upload, validators=image_validators)
    caption = models.CharField("Izoh", max_length=255, blank=True)

    CACHE_TAGS = ("news",)

    class Meta(OrderedModel.Meta):
        verbose_name = "Yangilik rasmi"
        verbose_name_plural = "Yangilik rasmlari"


class Film(RichTextMixin, SluggedModel, PublishableModel, TimeStampedModel, OrderedModel):
    """Video stories about companies of the region (Uz Made and others)."""

    title = models.CharField("Sarlavha", max_length=255)
    company = models.CharField("Kompaniya", max_length=255)
    owner_name = models.CharField("Kompaniya rahbari / egasi", max_length=255, blank=True)
    description = models.TextField("Tavsif", blank=True)
    video_url = models.URLField("Video havolasi (YouTube va b.)", blank=True)
    video_file = models.FileField(
        "Video fayl", upload_to=videos_upload, blank=True, validators=video_validators,
        help_text="YouTube havolasi o‘rniga to‘g‘ridan-to‘g‘ri yuklash mumkin (mp4, webm)",
    )
    cover = models.ImageField("Muqova", upload_to=covers_upload, blank=True, validators=image_validators)
    duration = models.CharField("Davomiyligi", max_length=20, blank=True, help_text="Masalan: 12:40")

    RICH_TEXT_FIELDS = ("description",)
    CACHE_TAGS = ("films",)

    class Meta:
        verbose_name = "Film"
        verbose_name_plural = "Filmlar"
        ordering = ["order", "-published_at"]

    def __str__(self):
        return self.title


class Announcement(RichTextMixin, SluggedModel, PublishableModel, TimeStampedModel):
    """Announcements and upcoming events."""

    class Kind(models.TextChoices):
        ANNOUNCEMENT = "announcement", "E’lon"
        EVENT = "event", "Tadbir"
        TENDER = "tender", "Tanlov"

    title = models.CharField("Sarlavha", max_length=255)
    kind = models.CharField("Turi", max_length=20, choices=Kind.choices, default=Kind.ANNOUNCEMENT, db_index=True)
    excerpt = models.TextField("Qisqa mazmun", max_length=600, blank=True)
    body = models.TextField("Matn", blank=True)
    cover = models.ImageField("Muqova", upload_to=covers_upload, blank=True, validators=image_validators)
    event_date = models.DateTimeField("Boshlanish sanasi va vaqti", null=True, blank=True, db_index=True)
    ends_at = models.DateTimeField("Amal qilish muddati (tugash)", null=True, blank=True)
    location = models.CharField("Manzil", max_length=255, blank=True)
    participants = models.PositiveIntegerField("Ishtirokchilar soni", null=True, blank=True)
    registration_url = models.URLField("Ro‘yxatdan o‘tish havolasi", blank=True)
    is_featured = models.BooleanField("Asosiy tadbir", default=False)
    gallery = models.ForeignKey(
        "content.Gallery", verbose_name="Fotohisobot", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="announcements",
    )

    RICH_TEXT_FIELDS = ("body",)
    CACHE_TAGS = ("announcements",)

    class Meta:
        verbose_name = "E’lon"
        verbose_name_plural = "E’lonlar va tadbirlar"
        ordering = ["-event_date", "-published_at"]

    def __str__(self):
        return self.title


class Gallery(SluggedModel, PublishableModel, TimeStampedModel):
    """Photo reports of events."""

    title = models.CharField("Sarlavha", max_length=255)
    description = models.TextField("Tavsif", blank=True)
    event_date = models.DateField("Tadbir sanasi", null=True, blank=True)
    location = models.CharField("Joy", max_length=255, blank=True)
    cover = models.ImageField("Muqova", upload_to=covers_upload, blank=True, validators=image_validators)

    CACHE_TAGS = ("galleries",)

    class Meta:
        verbose_name = "Fotohisobot"
        verbose_name_plural = "Fotohisobotlar"
        ordering = ["-event_date", "-created_at"]

    def __str__(self):
        return self.title


class GalleryImage(OrderedModel):
    gallery = models.ForeignKey(Gallery, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField("Rasm", upload_to=gallery_upload, validators=image_validators)
    caption = models.CharField("Izoh", max_length=255, blank=True)

    CACHE_TAGS = ("galleries",)

    class Meta(OrderedModel.Meta):
        verbose_name = "Fotohisobot rasmi"
        verbose_name_plural = "Fotohisobot rasmlari"
