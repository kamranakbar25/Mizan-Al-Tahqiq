from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from library.models import Book, KnowledgeCategory, SourceRecord


class Phase12APITests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.researcher = User.objects.create_user(
            username="phase12-researcher", password="Strong-Test-Password-2026!"
        )
        self.staff = User.objects.create_user(
            username="phase12-staff", password="Strong-Test-Password-2026!", is_staff=True
        )
        self.book = Book.objects.create(title="API test book", language="ar")

    def sign_in(self, username):
        response = self.client.post("/accounts/login/", {
            "username": username,
            "password": "Strong-Test-Password-2026!",
        })
        self.assertEqual(response.status_code, 302)

    def test_category_api_requires_login(self):
        response = self.client.get("/api/categories/")
        self.assertIn(response.status_code, (302, 401, 403))

    def test_researcher_can_create_category(self):
        self.sign_in("phase12-researcher")
        response = self.client.post("/api/categories/", {
            "name": "Hadith Sciences", "slug": "hadith-sciences", "is_active": True,
        })
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(KnowledgeCategory.objects.filter(slug="hadith-sciences").exists())

    def test_category_parent_filter_returns_root_categories(self):
        root = KnowledgeCategory.objects.create(name="Hadith", slug="hadith")
        KnowledgeCategory.objects.create(
            name="Hadith Sciences", slug="hadith-sciences", parent=root
        )
        self.sign_in("phase12-researcher")
        response = self.client.get("/api/categories/?parent=root")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["slug"] for row in response.json()["results"]], ["hadith"])

    def test_book_can_be_filtered_by_category_and_language(self):
        category = KnowledgeCategory.objects.create(name="Tafsir", slug="tafsir")
        self.book.categories.add(category)
        self.sign_in("phase12-researcher")
        response = self.client.get(f"/api/books/?category={category.pk}&language=ar")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_researcher_can_register_source_but_cannot_verify_it(self):
        self.sign_in("phase12-researcher")
        created = self.client.post("/api/sources/", {
            "name": "Test Digital Library", "source_type": "digital_library",
        })
        self.assertEqual(created.status_code, 201, created.content)
        source = SourceRecord.objects.get(name="Test Digital Library")
        self.assertEqual(source.rights_status, "unknown")
        self.assertEqual(source.verification_status, "unverified")
        changed = self.client.patch(
            f"/api/sources/{source.pk}/",
            {"verification_status": "verified"},
            content_type="application/json",
        )
        self.assertEqual(changed.status_code, 400)

    def test_staff_can_verify_source_and_is_recorded(self):
        source = SourceRecord.objects.create(name="Staff verified source")
        self.sign_in("phase12-staff")
        response = self.client.patch(
            f"/api/sources/{source.pk}/",
            {"verification_status": "verified"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        source.refresh_from_db()
        self.assertEqual(source.verification_status, "verified")
        self.assertEqual(source.verified_by, self.staff)
        self.assertIsNotNone(source.verified_at)

    def test_document_upload_rejects_unsupported_extension(self):
        self.sign_in("phase12-researcher")
        upload = SimpleUploadedFile("payload.exe", b"not a supported document")
        response = self.client.post(
            "/api/documents/", {"book": self.book.pk, "file": upload}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.json())

    def test_document_upload_rejects_empty_file(self):
        self.sign_in("phase12-researcher")
        upload = SimpleUploadedFile("empty.txt", b"")
        response = self.client.post(
            "/api/documents/", {"book": self.book.pk, "file": upload}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.json())
