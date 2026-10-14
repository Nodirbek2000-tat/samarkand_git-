"""
Give or take rights from the command line — handy on a fresh server before anyone can open /admin:

    python manage.py set_role +998901234567 admin       # by phone (Telegram-registered)
    python manage.py set_role @telegram_username editor
    python manage.py set_role admin user                 # by site login
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.telegram import normalize_phone

ROLES = {"user": "Foydalanuvchi", "editor": "Muharrir", "admin": "Administrator"}


class Command(BaseCommand):
    help = "Foydalanuvchi rolini o‘zgartirish: user | editor | admin"

    def add_arguments(self, parser):
        parser.add_argument("who", help="telefon (+998…), @telegram_username yoki sayt logini")
        parser.add_argument("role", choices=list(ROLES))

    def handle(self, *args, who, role, **options):
        users = get_user_model().objects.select_related("telegram")
        who = who.strip()
        if who.startswith("@"):
            user = users.filter(telegram__username__iexact=who[1:]).first()
        elif who.lstrip("+").isdigit():
            user = users.filter(telegram__phone=normalize_phone(who)).first()
        else:
            user = users.filter(username=who).first()
        if user is None:
            raise CommandError(f"“{who}” topilmadi. Telegram foydalanuvchisi avval botda ro‘yxatdan o‘tishi kerak.")

        user.is_staff = role in ("editor", "admin")
        user.is_superuser = role == "admin"
        user.is_active = True
        user.save(update_fields=["is_staff", "is_superuser", "is_active"])
        self.stdout.write(self.style.SUCCESS(f"{user.get_full_name() or user.username}: {ROLES[role]}"))
