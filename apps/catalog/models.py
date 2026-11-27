"""
«Made in Samarkand» — the catalog of goods produced in the region: categories, the companies that make them
and their products. Filled from the former madeinsam.uz catalog (see the import_catalog command) and edited
in the admin afterwards.
"""

from django.db import models

from apps.core.models import OrderedModel, SluggedModel, TimeStampedModel, _UploadTo
from apps.core.validators import image_validators

catalog_upload = _UploadTo("catalog")


class Category(SluggedModel, TimeStampedModel, OrderedModel):
    title = models.CharField("Nomi", max_length=200)
    image = models.ImageField("Rasm", upload_to=catalog_upload, blank=True, validators=image_validators)
    source_id = models.PositiveIntegerField(null=True, blank=True, unique=True, editable=False)

    CACHE_TAGS = ("catalog",)

    class Meta(OrderedModel.Meta):
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self):
        return self.title


class Company(SluggedModel, TimeStampedModel):
    title = models.CharField("Korxona nomi", max_length=255)
    category = models.ForeignKey(Category, related_name="companies", on_delete=models.PROTECT, verbose_name="Kategoriya")
    logo = models.ImageField("Logotip", upload_to=catalog_upload, blank=True, validators=image_validators)
    description = models.TextField("Korxona haqida", blank=True)
    address = models.CharField("Manzil", max_length=255, blank=True)
    phone = models.CharField("Savdo bo‘limi telefoni", max_length=60, blank=True)
    sales_manager = models.CharField("Savdo bo‘limi rahbari", max_length=255, blank=True)
    email = models.EmailField("Email", blank=True)
    website = models.URLField("Veb-sayt", blank=True)
    telegram = models.URLField("Telegram", blank=True)
    instagram = models.URLField("Instagram", blank=True)
    facebook = models.URLField("Facebook", blank=True)
    youtube = models.URLField("YouTube", blank=True)
    whatsapp = models.CharField("WhatsApp", max_length=200, blank=True)
    is_published = models.BooleanField("Saytda ko‘rsatish", default=True, db_index=True)
    source_id = models.PositiveIntegerField(null=True, blank=True, unique=True, editable=False)

    CACHE_TAGS = ("catalog",)

    class Meta:
        verbose_name = "Korxona"
        verbose_name_plural = "Korxonalar"
        ordering = ["title"]

    def __str__(self):
        return self.title


class CompanyImage(OrderedModel):
    company = models.ForeignKey(Company, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField("Rasm", upload_to=catalog_upload, validators=image_validators)

    CACHE_TAGS = ("catalog",)

    class Meta(OrderedModel.Meta):
        verbose_name = "Korxona rasmi"
        verbose_name_plural = "Korxona rasmlari"


class Product(TimeStampedModel):
    company = models.ForeignKey(Company, related_name="products", on_delete=models.CASCADE, verbose_name="Korxona")
    category = models.ForeignKey(Category, related_name="products", on_delete=models.PROTECT, verbose_name="Kategoriya")
    name = models.CharField("Mahsulot nomi", max_length=255)
    description = models.TextField("Tavsif", blank=True)
    is_published = models.BooleanField("Saytda ko‘rsatish", default=True, db_index=True)
    source_id = models.PositiveIntegerField(null=True, blank=True, unique=True, editable=False)

    CACHE_TAGS = ("catalog",)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductImage(OrderedModel):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField("Rasm", upload_to=catalog_upload, validators=image_validators)

    CACHE_TAGS = ("catalog",)

    class Meta(OrderedModel.Meta):
        verbose_name = "Mahsulot rasmi"
        verbose_name_plural = "Mahsulot rasmlari"
