from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Umumiy sozlamalar"

    def ready(self):
        from .revalidate import connect_signals

        connect_signals()
