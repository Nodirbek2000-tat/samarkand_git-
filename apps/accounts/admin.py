from django.contrib import admin

from .models import BotBroadcast, BotChannel, BotMessage, BotState, BotSubscriber, LoginCode, TelegramAccount


@admin.register(BotSubscriber)
class BotSubscriberAdmin(admin.ModelAdmin):
    list_display = ["__str__", "username", "telegram_id", "is_blocked", "joined_at", "last_seen_at"]
    list_filter = ["is_blocked"]
    search_fields = ["first_name", "last_name", "username", "telegram_id"]
    readonly_fields = ["telegram_id", "chat_id", "joined_at", "last_seen_at"]


@admin.register(BotChannel)
class BotChannelAdmin(admin.ModelAdmin):
    list_display = ["__str__", "username", "chat_id", "is_active", "created_at"]
    list_filter = ["is_active"]


@admin.register(BotBroadcast)
class BotBroadcastAdmin(admin.ModelAdmin):
    list_display = ["__str__", "kind", "status", "sent", "failed", "total", "created_at", "finished_at"]
    list_filter = ["kind", "status"]
    readonly_fields = ["source", "file_id", "cursor", "total", "sent", "failed", "created_at", "started_at", "finished_at"]


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
