import shutil
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix="ys-media-")


@override_settings(MEDIA_ROOT=MEDIA)
@mock.patch("apps.core.revalidate._queue", lambda tags: None)
class FilmVideoTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(User.objects.create_user("ed", password="x-very-strong-1", is_staff=True))

    def test_film_needs_link_or_file(self):
        r = self.client.post("/api/films", {"title": "Film", "company": "SAG"}, format="multipart")
        self.assertEqual(r.status_code, 400)
        self.assertIn("video_url", r.json().get("errors", r.json()))

    def test_uploaded_video_is_served_and_playable(self):
        clip = SimpleUploadedFile("clip.mp4", b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 512, content_type="video/mp4")
        r = self.client.post("/api/films", {"title": "Film", "company": "SAG", "video_file": clip, "is_published": "true"}, format="multipart")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertTrue(r.json()["video_file"].startswith("/media/videos/"))
        self.assertEqual(APIClient().get(f"/api/films/{r.json()['slug']}").json()["video_file"], r.json()["video_file"])

    def test_only_video_formats_are_accepted(self):
        bad = SimpleUploadedFile("clip.exe", b"MZ" + b"\x00" * 64, content_type="application/octet-stream")
        r = self.client.post("/api/films", {"title": "Film", "company": "SAG", "video_file": bad}, format="multipart")
        self.assertEqual(r.status_code, 400)
