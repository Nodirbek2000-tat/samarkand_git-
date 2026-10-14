from django.db import models

from apps.core.models import OrderedModel, PublishableModel, RichTextMixin, TimeStampedModel, covers_upload
from apps.core.validators import image_validators


class ForumEdition(RichTextMixin, PublishableModel, TimeStampedModel):
    """One annual Industrialists' Forum (e.g. Forum 2024 — results of 2023)."""

    year = models.PositiveSmallIntegerField("Forum yili", unique=True)
    results_year = models.PositiveSmallIntegerField("Yakunlar yili")
    title = models.CharField("Sarlavha", max_length=255)
    dates = models.CharField("O‘tkazilgan sanalar", max_length=120, blank=True, help_text="Masalan: 16–17 may 2024")
    location = models.CharField("O‘tkazilgan joy", max_length=255, blank=True)
    intro = models.TextField("Kirish matni", blank=True)
    cover = models.ImageField("Muqova", upload_to=covers_upload, blank=True, validators=image_validators)
    gallery = models.ForeignKey(
        "content.Gallery", verbose_name="Fotohisobot", null=True, blank=True, on_delete=models.SET_NULL
    )

    RICH_TEXT_FIELDS = ("intro",)
    CACHE_TAGS = ("forum",)

    class Meta:
        verbose_name = "Forum"
        verbose_name_plural = "Sanoatchilar forumlari"
        ordering = ["-year"]

    def __str__(self):
        return f"Forum {self.year}"


class Nomination(OrderedModel):
    edition = models.ForeignKey(ForumEdition, related_name="nominations", on_delete=models.CASCADE)
    title = models.CharField("Nominatsiya", max_length=400)

    CACHE_TAGS = ("forum",)

    class Meta(OrderedModel.Meta):
        verbose_name = "Nominatsiya"
        verbose_name_plural = "Nominatsiyalar"

    def __str__(self):
        return self.title


class Winner(OrderedModel):
    class Level(models.TextChoices):
        FIRST = "1", "I darajali diplom"
        SECOND = "2", "II darajali diplom"
        THIRD = "3", "III darajali diplom"
        WINNER = "winner", "G‘olib"
        SPECIAL = "special", "Maxsus e’tirof"

    nomination = models.ForeignKey(Nomination, related_name="winners", on_delete=models.CASCADE)
    level = models.CharField("Daraja", max_length=10, choices=Level.choices, default=Level.WINNER)
    name = models.CharField("G‘olib (korxona / shaxs)", max_length=400)
    note = models.CharField("Izoh (hudud, brend)", max_length=255, blank=True)

    CACHE_TAGS = ("forum",)

    class Meta(OrderedModel.Meta):
        verbose_name = "G‘olib"
        verbose_name_plural = "G‘oliblar"

    def __str__(self):
        return self.name
