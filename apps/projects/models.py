from django.db import models

from apps.core.models import (
    OrderedModel,
    PublishableModel,
    RichTextMixin,
    SluggedModel,
    TimeStampedModel,
    covers_upload,
    documents_upload,
    gallery_upload,
)
from apps.core.validators import document_validators, image_validators


class Project(RichTextMixin, SluggedModel, PublishableModel, TimeStampedModel, OrderedModel):
    class Category(models.TextChoices):
        SOCIAL = "social", "Ijtimoiy loyiha"
        SCIENCE = "science", "Ilmiy ishlanma"
        STARTUP = "startup", "Yoshlar startapi"
        CLUB = "club", "Biznes klub"
        MEDIA = "media", "Media loyiha"
        CATALOG = "catalog", "Katalog"
        FORUM = "forum", "Forum"
        OTHER = "other", "Boshqa"

    class Status(models.TextChoices):
        ACTIVE = "active", "Amaldagi"
        COMPLETED = "completed", "Amalga oshirilgan"
        PLANNED = "planned", "Rejalashtirilgan"

    title = models.CharField("Nomi", max_length=255)
    category = models.CharField("Yo‘nalish", max_length=20, choices=Category.choices, default=Category.SOCIAL, db_index=True)
    status = models.CharField("Holati", max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    summary = models.TextField("Qisqa tavsif", max_length=700, blank=True)
    body = models.TextField("To‘liq matn", blank=True)
    objectives = models.TextField("Maqsadlar", blank=True)
    expected_results = models.TextField("Kutilayotgan natijalar", blank=True)
    metrics = models.CharField("Asosiy ko‘rsatkichlar (qisqa)", max_length=255, blank=True)
    stats = models.JSONField(
        "Raqamlar",
        default=list,
        blank=True,
        help_text='Ro‘yxat: [{"value": "406", "label": "korxona"}, ...]',
    )
    cover = models.ImageField("Muqova", upload_to=covers_upload, blank=True, validators=image_validators)
    video_url = models.URLField("Video havolasi", blank=True)
    website_url = models.URLField("Veb-sayt", blank=True)
    telegram_url = models.URLField("Telegram", blank=True)
    instagram_url = models.URLField("Instagram", blank=True)
    started_on = models.DateField("Boshlangan sana", null=True, blank=True)
    finished_on = models.DateField("Yakunlangan sana", null=True, blank=True)
    budget = models.CharField("Moliyalashtirish hajmi", max_length=120, blank=True)
    is_featured = models.BooleanField("Bosh sahifada ko‘rsatish", default=False)

    RICH_TEXT_FIELDS = ("body", "objectives", "expected_results")
    CACHE_TAGS = ("projects",)

    class Meta:
        verbose_name = "Loyiha"
        verbose_name_plural = "Loyihalar"
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title


class ProjectImage(OrderedModel):
    project = models.ForeignKey(Project, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField("Rasm", upload_to=gallery_upload, validators=image_validators)
    caption = models.CharField("Izoh", max_length=255, blank=True)

    CACHE_TAGS = ("projects",)

    class Meta(OrderedModel.Meta):
        verbose_name = "Loyiha rasmi"
        verbose_name_plural = "Loyiha rasmlari"


class ProjectDocument(OrderedModel):
    project = models.ForeignKey(Project, related_name="documents", on_delete=models.CASCADE)
    title = models.CharField("Hujjat nomi", max_length=255)
    file = models.FileField("Fayl", upload_to=documents_upload, validators=document_validators)

    CACHE_TAGS = ("projects",)

    class Meta(OrderedModel.Meta):
        verbose_name = "Loyiha hujjati"
        verbose_name_plural = "Loyiha hujjatlari"

    def __str__(self):
        return self.title


class ProjectParticipant(OrderedModel):
    """Companies and people behind a project — e.g. the initiators of the Siyob canal project."""

    project = models.ForeignKey(Project, related_name="participants", on_delete=models.CASCADE)
    company = models.CharField("Kompaniya", max_length=255)
    person = models.CharField("Mas’ul shaxs", max_length=255, blank=True)
    role = models.CharField("Roli", max_length=120, blank=True, default="Tashabbuskor")
    contribution = models.CharField("Hissasi", max_length=255, blank=True)

    CACHE_TAGS = ("projects",)

    class Meta(OrderedModel.Meta):
        verbose_name = "Loyiha ishtirokchisi"
        verbose_name_plural = "Loyiha ishtirokchilari"

    def __str__(self):
        return self.company
