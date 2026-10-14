import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class TelegramAccount(models.Model):
    """A site visitor registered through the Telegram bot (phone number shared from Telegram)."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="telegram", on_delete=models.CASCADE)
    telegram_id = models.BigIntegerField("Telegram ID", unique=True)
    username = models.CharField("Telegram username", max_length=64, blank=True)
    phone = models.CharField("Telefon", max_length=32, db_index=True)
    first_name = models.CharField("Ism (Telegram)", max_length=128, blank=True)
    last_name = models.CharField("Familiya (Telegram)", max_length=128, blank=True)
    company = models.CharField("Kompaniya", max_length=255, blank=True)
    position = models.CharField("Lavozim", max_length=255, blank=True)
    chat_id = models.BigIntegerField("Chat ID")
    is_blocked_bot = models.BooleanField("Botni bloklagan", default=False)
    created_at = models.DateTimeField("Ro‘yxatdan o‘tgan", auto_now_add=True)
    last_login_at = models.DateTimeField("Oxirgi kirish", null=True, blank=True)

    class Meta:
        verbose_name = "Telegram foydalanuvchi"
        verbose_name_plural = "Telegram foydalanuvchilar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.first_name} ({self.phone})"


def _hash_code(code: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), code.encode(), hashlib.sha256).hexdigest()


class LoginCodeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(used_at__isnull=True, expires_at__gt=timezone.now())


class LoginCode(models.Model):
    """One-time 6-digit code sent by the bot. Only a keyed hash is stored."""

    account = models.ForeignKey(TelegramAccount, related_name="codes", on_delete=models.CASCADE)
    code_hash = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)

    objects = LoginCodeQuerySet.as_manager()

    class Meta:
        verbose_name = "Kirish kodi"
        verbose_name_plural = "Kirish kodlari"
        ordering = ["-created_at"]

    @classmethod
    def issue(cls, account: TelegramAccount) -> str:
        """Invalidate the account's previous codes and create a fresh one, unique among active codes."""
        now = timezone.now()
        cls.objects.filter(account=account, used_at__isnull=True).update(used_at=now)
        for _ in range(20):
            code = f"{secrets.randbelow(1_000_000):06d}"
            digest = _hash_code(code)
            if not cls.objects.active().filter(code_hash=digest).exists():
                break
        cls.objects.create(
            account=account,
            code_hash=digest,
            expires_at=now + timedelta(seconds=settings.TELEGRAM_LOGIN_CODE_TTL),
        )
        return code

    @classmethod
    def redeem(cls, code: str) -> TelegramAccount | None:
        code = "".join(ch for ch in code if ch.isdigit())
        if len(code) != 6:
            return None
        item = cls.objects.active().select_related("account__user").filter(code_hash=_hash_code(code)).first()
        if item is None:
            return None
        # atomic single use: only the request that flips used_at wins
        claimed = cls.objects.filter(pk=item.pk, used_at__isnull=True).update(used_at=timezone.now())
        return item.account if claimed else None


class BotState(models.Model):
    """Single row describing the separate aiogram bot (samarkand_bot): who it is and when it last called in."""

    ONLINE_WINDOW = timedelta(seconds=60)

    username = models.CharField("Bot username", max_length=64, blank=True)
    first_name = models.CharField("Bot nomi", max_length=128, blank=True)
    started_at = models.DateTimeField("Ishga tushgan", null=True, blank=True)
    last_seen_at = models.DateTimeField("Oxirgi aloqa", null=True, blank=True)

    class Meta:
        verbose_name = "Bot holati"
        verbose_name_plural = "Bot holati"

    def __str__(self):
        return f"@{self.username}" if self.username else "Bot (hali ulanmagan)"

    @classmethod
    def get(cls) -> "BotState":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def online(self) -> bool:
        return bool(self.last_seen_at and timezone.now() - self.last_seen_at < self.ONLINE_WINDOW)


class BotMessage(models.Model):
    """Outbox: the site queues messages here, the bot polls /api/bot/outbox and delivers them."""

    class Status(models.TextChoices):
        PENDING = "pending", "Navbatda"
        SENT = "sent", "Yuborildi"
        FAILED = "failed", "Yetkazilmadi"

    MAX_ATTEMPTS = 5

    account = models.ForeignKey(
        TelegramAccount, verbose_name="Foydalanuvchi", related_name="messages", null=True, blank=True, on_delete=models.SET_NULL
    )
    chat_id = models.BigIntegerField("Chat ID")
    text = models.TextField("Matn (HTML)")
    status = models.CharField("Holati", max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    attempts = models.PositiveSmallIntegerField("Urinishlar", default=0)
    last_error = models.CharField("Oxirgi xato", max_length=255, blank=True)
    created_at = models.DateTimeField("Yaratilgan", auto_now_add=True)
    sent_at = models.DateTimeField("Yuborilgan", null=True, blank=True)

    class Meta:
        verbose_name = "Bot xabari"
        verbose_name_plural = "Bot xabarlari (navbat)"
        ordering = ["id"]

    def __str__(self):
        return f"#{self.pk} → {self.chat_id} ({self.get_status_display()})"
