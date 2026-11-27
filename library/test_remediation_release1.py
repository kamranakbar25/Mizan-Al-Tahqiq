from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from library.models import Book, KnowledgeCategory, SourceRecord, SourceVerificationEvent


class RemediationRelease1Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.researcher = User.objects.create_user(
            username="remediation-researcher", password="Strong-Test-Password-2026!"
        )
        self.staff = User.objects.create_user(
            username="remediation-staff", password="Strong-Test-Password-2026!", is_staff=True
        )
        self.book = Book.objects.create(title="Remediation test book")

    def login(self, username):
        response = self.client.post("/accounts/login/", {
            "username": username,
            "password": "Strong-Test-Password-2026!",
        })
        self.assertEqual(response.status_code, 302)

    def test_researcher_cannot_delete_book(self):
        self.login("remediation-researcher")
        response = self.client.delete(f"/api/books/{self.book.pk}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())

    def test_staff_can_delete_book(self):
        self.login("remediation-staff")
        response = self.client.delete(f"/api/books/{self.book.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())

    def test_category_cannot_be_its_own_parent(self):
        category = KnowledgeCategory.objects.create(name="Category cycle", slug="category-cycle")
        self.login("remediation-researcher")
        response = self.client.patch(
            f"/api/categories/{category.pk}/",
            {"parent": category.pk},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_category_cannot_become_its_descendant_parent(self):
        parent = KnowledgeCategory.objects.create(name="Cycle parent", slug="cycle-parent")
        child = KnowledgeCategory.objects.create(name="Cycle child", slug="cycle-child", parent=parent)
        self.login("remediation-researcher")
        response = self.client.patch(
            f"/api/categories/{parent.pk}/",
            {"parent": child.pk},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_pdf_extension_with_non_pdf_content_is_rejected(self):
        self.login("remediation-researcher")
        upload = SimpleUploadedFile("fake.pdf", b"This is not a PDF")
        response = self.client.post("/api/documents/", {"book": self.book.pk, "file": upload})
        self.assertEqual(response.status_code, 400)

    def test_staff_source_decision_creates_verification_event(self):
        source = SourceRecord.objects.create(name="Verification history source")
        self.login("remediation-staff")
        response = self.client.patch(
            f"/api/sources/{source.pk}/",
            {"verification_status": "verified", "rights_status": "permission_required"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        event = SourceVerificationEvent.objects.get(source_record=source)
        self.assertEqual(event.new_status, "verified")
        self.assertEqual(event.new_rights_status, "permission_required")
        self.assertEqual(event.actor.username, "remediation-staff")

    def test_verification_history_api_is_read_only(self):
        source = SourceRecord.objects.create(name="Read-only history source")
        self.login("remediation-researcher")
        response = self.client.post("/api/source-verification-events/", {})
        self.assertEqual(response.status_code, 405)
