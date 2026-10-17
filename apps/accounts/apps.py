from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Foydalanuvchilar"

    def ready(self):
        from . import broadcast

        broadcast.connect()  # new items on the site → the bot's subscribers (when switched on)
