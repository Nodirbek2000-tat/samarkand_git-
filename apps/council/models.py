from django.db import models

from apps.core.models import (
    OrderedModel,
    PublishableModel,
    RichTextMixin,
    SluggedModel,
    TimeStampedModel,
    people_upload,
)
from apps.core.validators import image_validators


class Person(RichTextMixin, SluggedModel, TimeStampedModel, OrderedModel):
    full_name = models.CharField("F.I.Sh.", max_length=255)
    photo = models.ImageField("Surat", upload_to=people_upload, blank=True, validators=image_validators)
    bio = models.TextField("Biografiya", blank=True)
    is_active = models.BooleanField("Faol", default=True, db_index=True)

    SLUG_SOURCE = "full_name"
    RICH_TEXT_FIELDS = ("bio",)

    class Meta:
        abstract = True
        ordering = ["order", "full_name"]

    def __str__(self):
        return self.full_name


class CouncilMember(Person):
    """Members of the Public Advisory Council of Entrepreneurs."""

    company = models.CharField("Kompaniya", max_length=255, blank=True)
    position = models.CharField("Lavozimi", max_length=255, blank=True)
    industry = models.CharField("Soha", max_length=120, blank=True)
    website = models.URLField("Kompaniya sayti", blank=True)
    contact_email = models.EmailField("Aloqa email", blank=True)
    contact_phone = models.CharField("Aloqa telefoni", max_length=40, blank=True)
    show_contacts = models.BooleanField("Aloqa ma’lumotlarini saytda ko‘rsatish", default=False)
    joined_year = models.PositiveSmallIntegerField("A’zo bo‘lgan yili", null=True, blank=True)

    CACHE_TAGS = ("council",)

    class Meta(Person.Meta):
        verbose_name = "Kengash a’zosi"
        verbose_name_plural = "Kengash a’zolari"


class BoardMember(Person):
    """Members of the Board (Boshqaruv) of the Council."""

    class Role(models.TextChoices):
        CHAIRMAN = "chairman", "Boshqaruv raisi"
        DEPUTY = "deputy", "Rais o‘rinbosari"
        MEMBER = "member", "Boshqaruv a’zosi"
        SECRETARY = "secretary", "Kotib"

    role = models.CharField("Boshqaruvdagi lavozimi", max_length=20, choices=Role.choices, default=Role.MEMBER)
    workplace = models.CharField("Ish joyi va lavozimi", max_length=400, blank=True)

    CACHE_TAGS = ("council",)

    class Meta(Person.Meta):
        verbose_name = "Boshqaruv a’zosi"
        verbose_name_plural = "Boshqaruv"


class Leader(Person):
    """Executive office of the foundation (Rahbariyat)."""

    position = models.CharField("Lavozimi", max_length=255)
    organization = models.CharField("Tashkilot", max_length=255, blank=True)
    phone = models.CharField("Telefon", max_length=40, blank=True)
    email = models.EmailField("Email", blank=True)
    reception_hours = models.CharField("Qabul vaqti", max_length=120, blank=True)

    CACHE_TAGS = ("council",)

    class Meta(Person.Meta):
        verbose_name = "Rahbar"
        verbose_name_plural = "Rahbariyat"


class Meeting(RichTextMixin, SluggedModel, PublishableModel, TimeStampedModel):
    """Council meetings: date, host company, agenda and outcomes."""

    title = models.CharField("Sarlavha", max_length=255)
    date = models.DateField("Sana", db_index=True)
    host_company = models.CharField("Mezbon kompaniya", max_length=255, blank=True)
    location = models.CharField("Manzil", max_length=255, blank=True)
    agenda = models.TextField("Kun tartibi", blank=True)
    outcome = models.TextField("Natijalar va topshiriqlar", blank=True)
    gallery = models.ForeignKey(
        "content.Gallery", verbose_name="Fotohisobot", null=True, blank=True, on_delete=models.SET_NULL
    )

    RICH_TEXT_FIELDS = ("agenda", "outcome")
    CACHE_TAGS = ("council",)

    class Meta:
        verbose_name = "Kengash yig‘ilishi"
        verbose_name_plural = "Kengash yig‘ilishlari"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date:%d.%m.%Y} — {self.title}"


class Recognition(RichTextMixin, TimeStampedModel, OrderedModel):
    """Entrepreneurs publicly recognised by the Council."""

    full_name = models.CharField("F.I.Sh.", max_length=255)
    company = models.CharField("Kompaniya", max_length=255, blank=True)
    award = models.CharField("Mukofot / e’tirof", max_length=255)
    year = models.PositiveSmallIntegerField("Yil", db_index=True)
    photo = models.ImageField("Surat", upload_to=people_upload, blank=True, validators=image_validators)
    description = models.TextField("Tavsif", blank=True)
    is_published = models.BooleanField("E’lon qilingan", default=True, db_index=True)

    RICH_TEXT_FIELDS = ("description",)
    CACHE_TAGS = ("council",)

    class Meta:
        verbose_name = "E’tirof"
        verbose_name_plural = "Yutuqlarni e’tirof etish"
        ordering = ["-year", "order"]

    def __str__(self):
        return f"{self.full_name} — {self.award}"
