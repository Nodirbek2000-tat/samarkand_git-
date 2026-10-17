from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import BotMessage, BotState, LoginCode, TelegramAccount
from apps.inbox.models import Appeal

User = get_user_model()
NO_REVALIDATE = mock.patch("apps.core.revalidate._queue", lambda tags: None)
SECRET = "bot-test-secret"


@override_settings(BOT_API_SECRET=SECRET, TELEGRAM_BOT_USERNAME="")
class TelegramFlowTests(TestCase):
    """The bot (../samarkand_bot) drives these endpoints; here the test plays the bot."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        NO_REVALIDATE.start()

    @classmethod
    def tearDownClass(cls):
        NO_REVALIDATE.stop()
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.bot = APIClient(HTTP_X_BOT_SECRET=SECRET)

    def register(self, telegram_id=1001):
        r = self.bot.post(
            "/api/bot/register",
            {"telegram_id": telegram_id, "chat_id": telegram_id, "phone": "998901234567", "first_name": "Ali", "last_name": "Valiyev", "username": "ali_t"},
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.content)
        return r.json()["code"]

    def expire_cooldown(self):
        LoginCode.objects.update(created_at=timezone.now() - timedelta(minutes=1))

    # ------------------------------------------------------------ bot API
    def test_bot_api_requires_secret(self):
        for client in (APIClient(), APIClient(HTTP_X_BOT_SECRET="wrong")):
            self.assertEqual(client.post("/api/bot/code", {"telegram_id": 1}, format="json").status_code, 403)
            self.assertEqual(client.get("/api/bot/outbox").status_code, 403)

    @override_settings(BOT_API_SECRET="")
    def test_bot_api_closed_without_setting(self):
        self.assertEqual(APIClient(HTTP_X_BOT_SECRET="").get("/api/bot/outbox").status_code, 403)

    def test_unknown_user_must_share_phone(self):
        r = self.bot.post("/api/bot/code", {"telegram_id": 1001}, format="json")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["detail"], "not_registered")

    def test_register_creates_plain_site_user(self):
        code = self.register()
        self.assertEqual(len(code), 6)
        acc = TelegramAccount.objects.get()
        self.assertEqual(acc.phone, "+998901234567")
        self.assertEqual(acc.user.get_full_name(), "Ali Valiyev")
        self.assertFalse(acc.user.is_staff)
        self.assertFalse(acc.user.has_usable_password())

    def test_new_code_invalidates_previous_and_cooldown(self):
        first = self.register()
        r = self.bot.post("/api/bot/code", {"telegram_id": 1001}, format="json")
        self.assertEqual(r.status_code, 429)
        self.assertGreater(r.json()["retry_after"], 0)

        self.expire_cooldown()
        second = self.bot.post("/api/bot/code", {"telegram_id": 1001, "chat_id": 1001}, format="json").json()["code"]
        self.assertNotEqual(first, second)
        self.assertIsNone(LoginCode.redeem(first))
        self.assertIsNotNone(LoginCode.redeem(second))

    def test_blocked_site_user_gets_no_code(self):
        self.register()
        User.objects.filter(username="tg_1001").update(is_active=False)
        self.expire_cooldown()
        self.assertEqual(self.bot.post("/api/bot/code", {"telegram_id": 1001}, format="json").status_code, 403)

    def test_hello_reports_bot_username_to_site(self):
        self.assertFalse(APIClient().get("/api/auth/telegram").json()["enabled"])
        self.bot.post("/api/bot/hello", {"username": "ys_test_bot", "first_name": "Yangi Samarqand"}, format="json")
        cfg = APIClient().get("/api/auth/telegram").json()
        self.assertTrue(cfg["enabled"])
        self.assertEqual(cfg["bot_url"], "https://t.me/ys_test_bot?start=login")
        self.assertTrue(BotState.get().online)

    # ------------------------------------------------------------ site login
    def test_code_login_creates_session(self):
        code = self.register()
        c = APIClient()
        r = c.post("/api/auth/telegram/code", {"code": code[:3] + " " + code[3:]}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        me = c.get("/api/auth/me").json()
        self.assertTrue(me["authenticated"])
        self.assertFalse(me["user"]["is_staff"])
        self.assertEqual(me["user"]["telegram"]["phone"], "+998901234567")

    def test_code_is_single_use(self):
        code = self.register()
        self.assertEqual(APIClient().post("/api/auth/telegram/code", {"code": code}, format="json").status_code, 200)
        self.assertEqual(APIClient().post("/api/auth/telegram/code", {"code": code}, format="json").status_code, 400)

    def test_expired_code_rejected(self):
        code = self.register()
        LoginCode.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(APIClient().post("/api/auth/telegram/code", {"code": code}, format="json").status_code, 400)

    def test_blocked_user_cannot_login(self):
        code = self.register()
        User.objects.filter(username="tg_1001").update(is_active=False)
        self.assertEqual(APIClient().post("/api/auth/telegram/code", {"code": code}, format="json").status_code, 403)

    def test_site_user_cannot_use_admin_api(self):
        code = self.register()
        c = APIClient()
        c.post("/api/auth/telegram/code", {"code": code}, format="json")
        self.assertEqual(c.get("/api/dashboard").status_code, 403)
        self.assertEqual(c.post("/api/news", {"title": "x"}).status_code, 403)

    # ------------------------------------------------------------ cabinet + outbox
    def test_reply_is_queued_and_delivered_through_outbox(self):
        code = self.register()
        c = APIClient()
        c.post("/api/auth/telegram/code", {"code": code}, format="json")
        r = c.patch("/api/account/profile", {"first_name": "Alisher", "company": "SAG"}, format="json")
        self.assertEqual(r.json()["telegram"]["company"], "SAG")

        c.post("/api/appeals", {"full_name": "Alisher", "phone": "+998901234567", "message": "Gaz muammosi", "consent": True}, format="json")
        appeal = Appeal.objects.get()
        self.assertEqual(appeal.user.telegram.phone, "+998901234567")

        admin = User.objects.create_user("boss", password="x-very-strong-1", is_staff=True, is_superuser=True)
        a = APIClient()
        a.force_authenticate(admin)
        r = a.patch(f"/api/appeals/{appeal.pk}", {"status": "done", "reply": "Muammo <hal> qilindi"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertIs(r.json()["telegram_queued"], True)
        self.assertEqual(r.json()["account"]["phone"], "+998901234567")
        # an internal note alone tells the user nothing
        r = a.patch(f"/api/appeals/{appeal.pk}", {"admin_note": "ichki"}, format="json")
        self.assertIsNone(r.json()["telegram_queued"])

        outbox = self.bot.get("/api/bot/outbox").json()["messages"]
        self.assertEqual(len(outbox), 1)
        self.assertEqual(outbox[0]["chat_id"], 1001)
        self.assertIn("Muammo &lt;hal&gt; qilindi", outbox[0]["text"])  # escaped for Telegram HTML
        self.assertEqual(self.bot.post(f"/api/bot/outbox/{outbox[0]['id']}/ack", {"ok": True}, format="json").status_code, 200)
        self.assertEqual(self.bot.get("/api/bot/outbox").json()["messages"], [])
        self.assertEqual(BotMessage.objects.get().status, BotMessage.Status.SENT)

        mine = c.get("/api/account/submissions").json()
        self.assertEqual(mine[0]["reply"], "Muammo <hal> qilindi")
        self.assertEqual(mine[0]["status"], "done")

    def test_failed_delivery_retries_then_gives_up_and_blocked_user_is_skipped(self):
        self.register()
        acc = TelegramAccount.objects.get()
        msg = BotMessage.objects.create(account=acc, chat_id=acc.chat_id, text="x")
        for _ in range(BotMessage.MAX_ATTEMPTS - 1):
            self.bot.post(f"/api/bot/outbox/{msg.pk}/ack", {"ok": False, "error": "timeout"}, format="json")
        msg.refresh_from_db()
        self.assertEqual(msg.status, BotMessage.Status.PENDING)
        self.bot.post(f"/api/bot/outbox/{msg.pk}/ack", {"ok": False, "error": "timeout"}, format="json")
        msg.refresh_from_db()
        self.assertEqual(msg.status, BotMessage.Status.FAILED)

        other = BotMessage.objects.create(account=acc, chat_id=acc.chat_id, text="y")
        self.bot.post(f"/api/bot/outbox/{other.pk}/ack", {"ok": False, "error": "Forbidden: bot was blocked by the user", "blocked": True}, format="json")
        acc.refresh_from_db()
        self.assertTrue(acc.is_blocked_bot)
        from apps.accounts.telegram import notify

        self.assertFalse(notify(acc.user, "z"))  # nothing is queued for someone who blocked the bot

        # talking to the bot again clears the flag
        self.expire_cooldown()
        self.bot.post("/api/bot/code", {"telegram_id": 1001}, format="json")
        acc.refresh_from_db()
        self.assertFalse(acc.is_blocked_bot)

    def test_member_update_marks_blocked(self):
        self.register()
        self.bot.post("/api/bot/member", {"telegram_id": 1001, "blocked": True}, format="json")
        self.assertTrue(TelegramAccount.objects.get().is_blocked_bot)

    def test_anonymous_cannot_open_cabinet(self):
        self.assertEqual(APIClient().get("/api/account/submissions").status_code, 403)


@override_settings(BOT_API_SECRET=SECRET)
class RoleManagementTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        NO_REVALIDATE.start()

    @classmethod
    def tearDownClass(cls):
        NO_REVALIDATE.stop()
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.boss = User.objects.create_user("boss", password="x-very-strong-1", is_staff=True, is_superuser=True)
        self.admin = APIClient()
        self.admin.force_authenticate(self.boss)
        bot = APIClient(HTTP_X_BOT_SECRET=SECRET)
        r = bot.post("/api/bot/register", {"telegram_id": 77, "chat_id": 77, "phone": "998907777777", "first_name": "Vali"}, format="json")
        self.code = r.json()["code"]
        self.visitor = User.objects.get(username="tg_77")

    def test_list_filters_by_role(self):
        users = self.admin.get("/api/admin/users?role=user").json()["results"]
        self.assertEqual([u["id"] for u in users], [self.visitor.pk])
        self.assertEqual(users[0]["telegram"]["phone"], "+998907777777")
        counts = self.admin.get("/api/admin/users/counts").json()
        self.assertEqual((counts["admin"], counts["user"]), (1, 1))

    def test_grant_and_revoke_rights_for_telegram_user(self):
        r = self.admin.patch(f"/api/admin/users/{self.visitor.pk}", {"role": "editor"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["role"], "editor")
        # the promoted person signs in with the bot code as before and now reaches the panel API
        c = APIClient()
        c.post("/api/auth/telegram/code", {"code": self.code}, format="json")
        self.assertEqual(c.get("/api/dashboard").status_code, 200)
        self.assertEqual(c.get("/api/admin/users").status_code, 403)  # editors don't manage people

        self.admin.patch(f"/api/admin/users/{self.visitor.pk}", {"role": "admin"}, format="json")
        self.assertEqual(c.get("/api/admin/users").status_code, 200)

        self.admin.patch(f"/api/admin/users/{self.visitor.pk}", {"role": "user"}, format="json")
        self.assertEqual(c.get("/api/dashboard").status_code, 403)

    def test_cannot_demote_self_or_remove_last_admin(self):
        r = self.admin.patch(f"/api/admin/users/{self.boss.pk}", {"role": "editor"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.admin.patch(f"/api/admin/users/{self.boss.pk}", {"is_active": False}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_create_staff_needs_password_and_defaults_to_editor(self):
        self.assertEqual(self.admin.post("/api/admin/users", {"username": "muharrir"}, format="json").status_code, 400)
        r = self.admin.post("/api/admin/users", {"username": "muharrir", "password": "Yangi-parol-2026!", "first_name": "M"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()["role"], "editor")
        self.assertTrue(r.json()["has_password"])


@override_settings(BOT_API_SECRET=SECRET)
class BotAudienceTests(TestCase):
    """Subscribers, mandatory channels, the /admin rights and broadcasts (the test plays the bot)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        NO_REVALIDATE.start()

    @classmethod
    def tearDownClass(cls):
        NO_REVALIDATE.stop()
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.bot = APIClient(HTTP_X_BOT_SECRET=SECRET)

    def seen(self, telegram_id, **extra):
        r = self.bot.post("/api/bot/seen", {"telegram_id": telegram_id, "chat_id": telegram_id, "first_name": "A", **extra}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        return r.json()

    def test_seen_adds_subscriber_once_and_admin_flag_follows_site_role(self):
        from apps.accounts.models import BotSubscriber

        self.assertFalse(self.seen(5)["admin"])
        self.seen(5, username="new_name")
        self.assertEqual(BotSubscriber.objects.get().username, "new_name")
        self.bot.post("/api/bot/register", {"telegram_id": 5, "chat_id": 5, "phone": "998901112233"}, format="json")
        User.objects.filter(username="tg_5").update(is_staff=True, is_superuser=True)
        self.assertTrue(self.seen(5)["admin"])
        User.objects.filter(username="tg_5").update(is_superuser=False)  # editors do not get the bot's /admin
        self.assertFalse(self.seen(5)["admin"])

    def test_channels_add_list_delete(self):
        self.bot.post("/api/bot/channels", {"chat_id": -1001, "title": "Yangi Samarqand", "username": "@ys_news"}, format="json")
        channels = self.bot.get("/api/bot/channels").json()["channels"]
        self.assertEqual((channels[0]["username"], channels[0]["link"]), ("ys_news", "https://t.me/ys_news"))
        self.bot.delete("/api/bot/channels/-1001")
        self.assertEqual(self.bot.get("/api/bot/channels").json()["channels"], [])

    def test_ad_broadcast_walks_subscribers_and_marks_unreachable(self):
        from apps.accounts.models import BotBroadcast, BotSubscriber

        for i in (1, 2, 3):
            self.seen(i)
        r = self.bot.post("/api/bot/broadcasts", {"from_chat_id": 1, "message_id": 42}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        b = self.bot.get("/api/bot/broadcasts/next").json()["broadcast"]
        self.assertEqual((b["kind"], b["message_id"]), ("ad", 42))
        page = self.bot.get("/api/bot/subscribers", {"after": 0, "limit": 2}).json()["items"]
        self.assertEqual(len(page), 2)
        self.bot.post(f"/api/bot/broadcasts/{b['id']}/progress", {"sent": 1, "failed": 1, "blocked": [2], "cursor": page[-1][0]}, format="json")
        rest = self.bot.get("/api/bot/subscribers", {"after": page[-1][0]}).json()["items"]
        self.assertEqual([r[1] for r in rest], [3])
        r = self.bot.post(f"/api/bot/broadcasts/{b['id']}/progress", {"sent": 1, "done": True, "cursor": rest[-1][0]}, format="json")
        self.assertEqual(r.json(), {"status": "done", "sent": 2, "failed": 1, "total": 3})
        self.assertTrue(BotSubscriber.objects.get(chat_id=2).is_blocked)
        self.assertIsNone(self.bot.get("/api/bot/broadcasts/next").json()["broadcast"])
        self.assertEqual(BotBroadcast.objects.get().status, "done")

    def test_autopost_queues_new_items_once_only_when_switched_on(self):
        from apps.accounts.models import BotBroadcast
        from apps.content.models import News

        News.objects.create(title="Avval", excerpt="x", is_published=True)
        self.assertEqual(BotBroadcast.objects.count(), 0)  # switched off

        boss = User.objects.create_user("boss2", password="x-very-strong-1", is_staff=True, is_superuser=True)
        admin = APIClient()
        admin.force_authenticate(boss)
        self.assertTrue(admin.patch("/api/admin/bot", {"autopost": True}, format="json").json()["bot"]["autopost"])

        with self.captureOnCommitCallbacks(execute=True):
            news = News.objects.create(title="Forum natijalari", excerpt="<p>Eng ilg‘or korxonalar</p>", is_published=True)
        with self.captureOnCommitCallbacks(execute=True):
            news.title = "Forum natijalari (tahrir)"
            news.save()  # editing does not post again
        with self.captureOnCommitCallbacks(execute=True):
            News.objects.create(title="Qoralama", is_published=False)
        b = BotBroadcast.objects.get()
        self.assertEqual((b.kind, b.url), ("post", f"/news/{news.slug}"))
        self.assertIn("<b>Forum natijalari</b>", b.text)
        self.assertIn("Eng ilg‘or korxonalar", b.text)
        self.assertNotIn("<p>", b.text)

    def test_admin_panel_needs_administrator(self):
        editor = User.objects.create_user("ed", password="x-very-strong-1", is_staff=True)
        c = APIClient()
        c.force_authenticate(editor)
        self.assertEqual(c.get("/api/admin/bot").status_code, 403)
        self.assertEqual(APIClient().get("/api/admin/bot").status_code, 403)
