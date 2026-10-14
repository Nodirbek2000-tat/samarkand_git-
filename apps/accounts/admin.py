from django.contrib import admin

from .models import BotMessage, BotState, LoginCode, TelegramAccount


@admin.register(TelegramAccount)
class TelegramAccountAdmin(admin.ModelAdmin):
    list_display = ["__str__", "phone", "username", "company", "is_blocked_bot", "created_at", "last_login_at"]
    search_fields = ["phone", "username", "first_name", "last_name", "company"]
    readonly_fields = ["telegram_id", "chat_id", "created_at", "last_login_at"]


@admin.register(LoginCode)
class LoginCodeAdmin(admin.ModelAdmin):
    list_display = ["account", "created_at", "expires_at", "used_at"]
    readonly_fields = ["account", "code_hash", "created_at", "expires_at", "used_at"]

    def has_add_permission(self, request):
        return False


@admin.register(BotMessage)
class BotMessageAdmin(admin.ModelAdmin):
    list_display = ["__str__", "account", "status", "attempts", "created_at", "sent_at"]
    list_filter = ["status"]
    search_fields = ["text", "account__phone"]
    readonly_fields = ["account", "chat_id", "created_at", "sent_at", "attempts", "last_error"]


@admin.register(BotState)
class BotStateAdmin(admin.ModelAdmin):
    list_display = ["__str__", "started_at", "last_seen_at"]
    readonly_fields = ["username", "first_name", "started_at", "last_seen_at"]

    def has_add_permission(self, request):
        return False
