"""
Bridge between the site and the Telegram bot.

The bot is a separate aiogram project (../samarkand_bot). It owns the Telegram token and the
conversation; Django owns the data. The bot calls the internal /api/bot/* endpoints (shared
secret, see `bot_api.py`) to register users and fetch login codes, and polls an outbox
(`BotMessage`) for anything the site wants delivered — replies to appeals today, announcements later.

Nothing in here talks to Telegram directly.
"""

import html
import math

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import BotMessage, BotState, LoginCode, TelegramAccount

User = get_user_model()


class CodeCooldown(Exception):
    """A code was issued moments ago — protects against button mashing and code flooding."""

    def __init__(self, retry_after: int):
        super().__init__(f"retry after {retry_after}s")
        self.retry_after = retry_after


def esc(text: str) -> str:
    """Escape user-provided text for Telegram's HTML parse mode."""
    return html.escape(text or "", quote=False)


def normalize_phone(phone: str) -> str:
    phone = "".join(ch for ch in (phone or "") if ch.isdigit() or ch == "+").strip()
    if phone and not phone.startswith("+"):
        phone = "+" + phone
    return phone[:32]


@transaction.atomic
def register(*, telegram_id: int, chat_id: int, phone: str, first_name: str = "", last_name: str = "", username: str = ""):
    """Create or refresh the account for a Telegram user who shared their own contact. Returns (account, created)."""
    first_name, last_name = first_name.strip()[:128], last_name.strip()[:128]
    account = TelegramAccount.objects.select_for_update().select_related("user").filter(telegram_id=telegram_id).first()
    created = account is None
    if created:
        user = User(username=f"tg_{telegram_id}", first_name=first_name[:150], last_name=last_name[:150], is_staff=False)
        user.set_unusable_password()
        user.save()
        account = TelegramAccount(user=user, telegram_id=telegram_id)
    account.chat_id = chat_id
    account.phone = normalize_phone(phone)
    account.first_name = first_name
    account.last_name = last_name
    account.username = (username or "")[:64]
    account.is_blocked_bot = False
    account.save()
    return account, created


def touch(account: TelegramAccount, *, chat_id: int | None = None, username: str | None = None) -> None:
    """The user is talking to the bot right now: keep chat/username fresh and clear the 'blocked' flag."""
    fields = []
    if chat_id and account.chat_id != chat_id:
        account.chat_id = chat_id
        fields.append("chat_id")
    if username is not None and account.username != username[:64]:
        account.username = username[:64]
        fields.append("username")
    if account.is_blocked_bot:
        account.is_blocked_bot = False
        fields.append("is_blocked_bot")
    if fields:
        account.save(update_fields=fields)


def issue_code(account: TelegramAccount) -> str:
    """Fresh one-time code for the account; raises CodeCooldown if one was issued just now."""
    last = account.codes.order_by("-created_at").values_list("created_at", flat=True).first()
    if last:
        elapsed = (timezone.now() - last).total_seconds()
        if elapsed < settings.TELEGRAM_CODE_COOLDOWN:
            raise CodeCooldown(math.ceil(settings.TELEGRAM_CODE_COOLDOWN - elapsed))
    return LoginCode.issue(account)


def notify(user, text: str) -> bool:
    """Queue a message (Telegram HTML) for a site user who registered through the bot. True if queued."""
    account = getattr(user, "telegram", None) if user else None
    if not account or account.is_blocked_bot:
        return False
    BotMessage.objects.create(account=account, chat_id=account.chat_id, text=text)
    return True


def bot_username() -> str:
    """Reported by the bot on start-up; the env setting is only a fallback."""
    return BotState.get().username or settings.TELEGRAM_BOT_USERNAME
