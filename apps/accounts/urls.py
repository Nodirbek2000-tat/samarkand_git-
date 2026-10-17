from django.urls import re_path

from . import bot_admin, bot_api, views

# Optional trailing slash: the frontend proxy forwards paths without one.
urlpatterns = [
    re_path(r"^auth/csrf/?$", views.CsrfView.as_view(), name="auth-csrf"),
    re_path(r"^auth/me/?$", views.MeView.as_view(), name="auth-me"),
    re_path(r"^auth/login/?$", views.LoginView.as_view(), name="auth-login"),
    re_path(r"^auth/logout/?$", views.LogoutView.as_view(), name="auth-logout"),
    re_path(r"^auth/change-password/?$", views.ChangePasswordView.as_view(), name="auth-change-password"),
    re_path(r"^auth/telegram/?$", views.TelegramConfigView.as_view(), name="auth-telegram-config"),
    re_path(r"^auth/telegram/code/?$", views.TelegramCodeLoginView.as_view(), name="auth-telegram-code"),
    re_path(r"^account/profile/?$", views.ProfileView.as_view(), name="account-profile"),
    re_path(r"^account/submissions/?$", views.MySubmissionsView.as_view(), name="account-submissions"),
    # internal API for the separate Telegram bot (../samarkand_bot), guarded by X-Bot-Secret
    re_path(r"^bot/hello/?$", bot_api.BotHelloView.as_view(), name="bot-hello"),
    re_path(r"^bot/register/?$", bot_api.BotRegisterView.as_view(), name="bot-register"),
    re_path(r"^bot/code/?$", bot_api.BotCodeView.as_view(), name="bot-code"),
    re_path(r"^bot/member/?$", bot_api.BotMemberView.as_view(), name="bot-member"),
    re_path(r"^bot/outbox/?$", bot_api.BotOutboxView.as_view(), name="bot-outbox"),
    re_path(r"^bot/outbox/(?P<pk>\d+)/ack/?$", bot_api.BotOutboxAckView.as_view(), name="bot-outbox-ack"),
    re_path(r"^bot/seen/?$", bot_api.BotSeenView.as_view(), name="bot-seen"),
    re_path(r"^bot/stats/?$", bot_api.BotStatsView.as_view(), name="bot-stats"),
    re_path(r"^bot/channels/?$", bot_api.BotChannelsView.as_view(), name="bot-channels"),
    re_path(r"^bot/channels/(?P<chat_id>-?\d+)/?$", bot_api.BotChannelDeleteView.as_view(), name="bot-channel-delete"),
    re_path(r"^bot/broadcasts/?$", bot_api.BotBroadcastCreateView.as_view(), name="bot-broadcast-create"),
    re_path(r"^bot/broadcasts/next/?$", bot_api.BotBroadcastNextView.as_view(), name="bot-broadcast-next"),
    re_path(r"^bot/broadcasts/(?P<pk>\d+)/progress/?$", bot_api.BotBroadcastProgressView.as_view(), name="bot-broadcast-progress"),
    re_path(r"^bot/subscribers/?$", bot_api.BotSubscribersView.as_view(), name="bot-subscribers"),
    # admin panel → «Telegram bot» (administrators)
    re_path(r"^admin/bot/?$", bot_admin.BotAdminView.as_view(), name="admin-bot"),
    re_path(r"^admin/bot/channels/(?P<pk>\d+)/?$", bot_admin.BotAdminChannelView.as_view(), name="admin-bot-channel"),
    re_path(r"^admin/bot/broadcasts/(?P<pk>\d+)/cancel/?$", bot_admin.BotAdminBroadcastCancelView.as_view(), name="admin-bot-cancel"),
]
