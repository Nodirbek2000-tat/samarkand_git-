from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.content.models import News
from apps.core.text import clean_html, uz_slugify
from apps.forum.models import ForumEdition
from apps.inbox.models import Appeal
from apps.projects.models import Project

User = get_user_model()

# keep tests independent of the frontend being up
NO_REVALIDATE = mock.patch("apps.core.revalidate._queue", lambda tags: None)


@override_settings(REST_FRAMEWORK={
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["apps.core.permissions.IsStaffOrReadOnly"],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_THROTTLE_RATES": {"public_forms": "1000/hour", "login": "1000/min"},
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
})
class ApiTests(TestCase):
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
        self.anon = APIClient()
        self.admin = User.objects.create_user("boss", password="x-very-strong-1", is_staff=True, is_superuser=True)
        self.editor = User.objects.create_user("editor", password="x-very-strong-2", is_staff=True)
        self.visitor = User.objects.create_user("visitor", password="x-very-strong-3")
        News.objects.create(title="Ochiq yangilik", is_published=True)
        News.objects.create(title="Qoralama yangilik", is_published=False)

    def client_for(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    # ------------------------------------------------------------ visibility
    def test_public_sees_only_published(self):
        titles = [n["title"] for n in self.anon.get("/api/news").json()["results"]]
        self.assertEqual(titles, ["Ochiq yangilik"])

    def test_draft_detail_is_404_for_public(self):
        draft = News.objects.get(title="Qoralama yangilik")
        self.assertEqual(self.anon.get(f"/api/news/{draft.slug}").status_code, 404)

    def test_staff_sees_drafts_and_can_filter(self):
        c = self.client_for(self.editor)
        self.assertEqual(c.get("/api/news").json()["count"], 2)
        self.assertEqual(c.get("/api/news?status=draft").json()["results"][0]["title"], "Qoralama yangilik")

    def test_lookup_by_id_and_slug(self):
        n = News.objects.get(title="Ochiq yangilik")
        self.assertEqual(self.anon.get(f"/api/news/{n.slug}").status_code, 200)
        self.assertEqual(self.anon.get(f"/api/news/{n.pk}").status_code, 200)

    # ------------------------------------------------------------ permissions
    def test_anonymous_cannot_write(self):
        self.assertEqual(self.anon.post("/api/news", {"title": "x"}).status_code, 403)

    def test_non_staff_user_cannot_write(self):
        self.assertEqual(self.client_for(self.visitor).post("/api/news", {"title": "x"}).status_code, 403)

    def test_editor_can_create_content(self):
        r = self.client_for(self.editor).post("/api/news", {"title": "Muharrir yozdi", "is_published": True}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()["slug"], "muharrir-yozdi")
        self.assertIsNotNone(r.json()["published_at"])

    def test_editor_cannot_read_inbox_or_users(self):
        c = self.client_for(self.editor)
        self.assertEqual(c.get("/api/appeals").status_code, 403)
        self.assertEqual(c.get("/api/admin/users").status_code, 403)
        self.assertEqual(c.patch("/api/settings", {"phone": "1"}, format="json").status_code, 403)

    def test_admin_reads_inbox(self):
        self.assertEqual(self.client_for(self.admin).get("/api/appeals").status_code, 200)

    def test_login_rejects_non_staff(self):
        r = self.anon.post("/api/auth/login", {"username": "visitor", "password": "x-very-strong-3"}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_login_and_me(self):
        r = self.anon.post("/api/auth/login", {"username": "boss", "password": "x-very-strong-1"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(self.anon.get("/api/auth/me").json()["authenticated"])

    # ------------------------------------------------------------ public forms
    def appeal(self, **extra):
        data = {"full_name": "Ali Valiyev", "phone": "+998901112233", "message": "Salom", "consent": True, **extra}
        return self.anon.post("/api/appeals", data, format="json")

    def test_public_appeal_is_saved_as_new(self):
        self.assertEqual(self.appeal().status_code, 201)
        self.assertEqual(Appeal.objects.get().status, "new")

    def test_honeypot_blocks_bots(self):
        self.assertEqual(self.appeal(hp="http://spam").status_code, 400)
        self.assertFalse(Appeal.objects.exists())

    def test_consent_is_required(self):
        self.assertEqual(self.appeal(consent=False).status_code, 400)

    def test_contact_needed(self):
        self.assertEqual(self.appeal(phone="", email="").status_code, 400)

    # ------------------------------------------------------------ forum & ordering
    def test_forum_structure_replace(self):
        ForumEdition.objects.create(year=2030, results_year=2029, title="Forum 2030", is_published=True)
        payload = {"nominations": [{"title": "Eng yaxshi brend", "winners": [{"level": "1", "name": "A MChJ"}, {"level": "2", "name": "B MChJ"}]}]}
        r = self.client_for(self.editor).put("/api/forum/2030/structure", payload, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["nominations"][0]["winners"][1]["name"], "B MChJ")
        self.assertEqual(self.anon.get("/api/forum/2030").json()["winners_count"], 2)

    def test_reorder(self):
        a = Project.objects.create(title="A", is_published=True, order=0)
        b = Project.objects.create(title="B", is_published=True, order=1)
        r = self.client_for(self.editor).post("/api/projects/reorder", {"ids": [b.pk, a.pk]}, format="json")
        self.assertEqual(r.status_code, 204)
        self.assertEqual([p["title"] for p in self.anon.get("/api/projects").json()["results"]], ["B", "A"])

    # ------------------------------------------------------------ search
    def test_search_apostrophes_words_and_ranking(self):
        Project.objects.create(title="Siyob kanali sohili", summary="Obodonlashtirish", is_published=True)
        Project.objects.create(title="Boshqa loyiha", body="<p>Siyob kanali bo‘yida <b>betonlash</b> ishlari</p>", is_published=True)
        News.objects.create(title="Kengash a’zolari yig‘ildi", is_published=True)
        search = lambda q: self.anon.get("/api/search", {"q": q}).json()["results"]
        # any apostrophe finds the typographic one
        self.assertEqual([r["title"] for r in search("a'zolari")], ["Kengash a’zolari yig‘ildi"])
        # every word must occur; a title match comes first
        titles = [r["title"] for r in search("kanali siyob")]
        self.assertEqual(titles, ["Siyob kanali sohili", "Boshqa loyiha"])
        # a match deep in the text shows the passage around it, without HTML
        deep = search("betonlash")[0]
        self.assertIn("betonlash", deep["text"])
        self.assertNotIn("<", deep["text"])
        # drafts and too-short queries return nothing
        self.assertEqual(search("Qoralama"), [])
        self.assertEqual(search("a"), [])


class TextTests(TestCase):
    def test_uzbek_slug(self):
        self.assertEqual(uz_slugify("Yoshlar startap‘lari — 2024"), "yoshlar-startaplari-2024")
        self.assertEqual(uz_slugify("Ўзбекистон ғолиблари"), "ozbekiston-goliblari")

    def test_html_is_sanitised(self):
        dirty = '<p onclick="x()">Salom<script>alert(1)</script> <a href="javascript:evil()">x</a></p>'
        clean = clean_html(dirty)
        self.assertNotIn("script", clean)
        self.assertNotIn("onclick", clean)
        self.assertNotIn("javascript:", clean)
        self.assertIn("Salom", clean)
