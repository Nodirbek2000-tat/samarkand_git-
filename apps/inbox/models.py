from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class InboxItem(TimeStampedModel):
    """Everything visitors send through the public forms shares a workflow."""

    class Status(models.TextChoices):
        NEW = "new", "Yangi"
        IN_PROGRESS = "in_progress", "Ko‘rib chiqilmoqda"
        DONE = "done", "Javob berilgan"
        ARCHIVED = "archived", "Arxiv"

    status = models.CharField("Holati", max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)
    admin_note = models.TextField("Administrator izohi", blank=True)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Mas’ul",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    ip_address = models.GenericIPAddressField("IP manzil", null=True, blank=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Ro‘yxatdan o‘tgan foydalanuvchi",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_submissions",
    )
    reply = models.TextField(
        "Foydalanuvchiga javob",
        blank=True,
        help_text="Kabinetda ko‘rinadi va foydalanuvchiga Telegram orqali yuboriladi",
    )
    replied_at = models.DateTimeField("Javob berilgan vaqt", null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class Appeal(InboxItem):
    """Appeals, proposals and contact-form messages."""

    class Kind(models.TextChoices):
        APPEAL = "appeal", "Murojaat"
        PROPOSAL = "proposal", "Taklif"
        COMPLAINT = "complaint", "Shikoyat"
        QUESTION = "question", "Savol"
        CONTACT = "contact", "Aloqa formasi"

    kind = models.CharField("Turi", max_length=20, choices=Kind.choices, default=Kind.APPEAL, db_index=True)
    full_name = models.CharField("F.I.Sh.", max_length=255)
    phone = models.CharField("Telefon", max_length=40, blank=True)
    email = models.EmailField("Email", blank=True)
    organization = models.CharField("Tashkilot", max_length=255, blank=True)
    subject = models.CharField("Mavzu", max_length=255, blank=True)
    message = models.TextField("Matn", max_length=5000)

    class Meta(InboxItem.Meta):
        verbose_name = "Murojaat"
        verbose_name_plural = "Murojaatlar"

    def __str__(self):
        return f"{self.full_name}: {self.subject or self.get_kind_display()}"


class CooperationRequest(InboxItem):
    class Kind(models.TextChoices):
        DOMESTIC = "domestic", "Mahalliy hamkorlik"
        INTERNATIONAL = "international", "Xalqaro hamkorlik"

    kind = models.CharField("Turi", max_length=20, choices=Kind.choices, default=Kind.DOMESTIC)
    organization = models.CharField("Tashkilot", max_length=255)
    contact_person = models.CharField("Aloqa uchun shaxs", max_length=255)
    phone = models.CharField("Telefon", max_length=40, blank=True)
    email = models.EmailField("Email", blank=True)
    website = models.URLField("Veb-sayt", blank=True)
    country = models.CharField("Davlat", max_length=120, blank=True)
    proposal = models.TextField("Hamkorlik taklifi", max_length=5000)

    class Meta(InboxItem.Meta):
        verbose_name = "Hamkorlik taklifi"
        verbose_name_plural = "Hamkorlik takliflari"

    def __str__(self):
        return self.organization


class MemberApplication(InboxItem):
    class Size(models.TextChoices):
        INDIVIDUAL = "individual", "YaTT / jismoniy shaxs"
        SMALL = "small", "Kichik korxona"
        MEDIUM = "medium", "O‘rta korxona"
        LARGE = "large", "Yirik korxona"
        HONORARY = "honorary", "Faxriy a’zolik"

    full_name = models.CharField("F.I.Sh.", max_length=255)
    company = models.CharField("Kompaniya", max_length=255, blank=True)
    position = models.CharField("Lavozimi", max_length=255, blank=True)
    size = models.CharField("Toifa", max_length=20, choices=Size.choices, default=Size.SMALL)
    industry = models.CharField("Faoliyat sohasi", max_length=255, blank=True)
    phone = models.CharField("Telefon", max_length=40)
    email = models.EmailField("Email", blank=True)
    message = models.TextField("Qo‘shimcha ma’lumot", max_length=3000, blank=True)

    class Meta(InboxItem.Meta):
        verbose_name = "A’zolik arizasi"
        verbose_name_plural = "A’zolik arizalari"

    def __str__(self):
        return f"{self.full_name} ({self.company})"
