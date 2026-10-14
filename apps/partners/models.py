from django.db import models

from apps.core.models import OrderedModel, TimeStampedModel, logos_upload
from apps.core.validators import image_validators


class Partner(TimeStampedModel, OrderedModel):
    class Kind(models.TextChoices):
        DOMESTIC = "domestic", "Mahalliy hamkor"
        INTERNATIONAL = "international", "Xalqaro hamkor"

    name = models.CharField("Nomi", max_length=255)
    kind = models.CharField("Turi", max_length=20, choices=Kind.choices, default=Kind.DOMESTIC, db_index=True)
    logo = models.ImageField("Logotip", upload_to=logos_upload, blank=True, validators=image_validators)
    country = models.CharField("Davlat", max_length=120, blank=True, default="O‘zbekiston")
    website = models.URLField("Veb-sayt", blank=True)
    description = models.TextField("Hamkorlik tavsifi", blank=True)
    is_published = models.BooleanField("Saytda ko‘rsatish", default=True, db_index=True)

    CACHE_TAGS = ("partners",)

    class Meta(OrderedModel.Meta):
        verbose_name = "Hamkor"
        verbose_name_plural = "Hamkorlar"

    def __str__(self):
        return self.name
