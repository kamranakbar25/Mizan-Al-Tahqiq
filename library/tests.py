import tempfile
from pathlib import Path

import pymupdf
from django.core.files import File
from django.test import TestCase, override_settings

from library.models import (
    Book, Document, ExtractionVersion, Page, ProcessingJob, TextBlock,
)
from library.services.universal_ingestion import (
    DuplicateDocumentError, inspect_document, process_document,
    queue_document, run_next_job,
)


class UniversalIngestionTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.settings = override_settings(MEDIA_ROOT=self.tmp.name)
        self.settings.enable()
        self.addCleanup(self.settings.disable)
        self.book = Book.objects.create(title="Test scholarly work", language="en")

    def make_pdf(self, filename="sample.pdf", content="Bismillah searchable test passage"):
        path = Path(self.tmp.name) / filename
        pdf = pymupdf.open()
        page = pdf.new_page()
        page.insert_text((72, 72), content)
        pdf.new_page()
        pdf.save(path)
        pdf.close()
        with path.open("rb") as handle:
            return Document.objects.create(
                book=self.book, file=File(handle, name=filename),
                original_filename=filename, file_size=path.stat().st_size,
            )

    def make_txt(self, filename="sample.txt", content="First paragraph.\n\nSecond paragraph."):
        path = Path(self.tmp.name) / filename
        path.write_text(content, encoding="utf-8")
        with path.open("rb") as handle:
            return Document.objects.create(
                book=self.book, file=File(handle, name=filename),
                original_filename=filename, file_size=path.stat().st_size,
            )

    def test_pdf_inspection_and_page_extraction(self):
        document = self.make_pdf()
        self.assertEqual(inspect_document(document.file.path)["unit_count"], 2)
        run = process_document(document)
        self.assertEqual(run.status, "partial")  # one page has no embedded text
        self.assertEqual(run.text_pages, 1)
        self.assertEqual(run.ocr_required_pages, 1)
        page = Page.objects.get(document=document, pdf_page_number=1)
        self.assertIn("searchable test", page.extracted_text)
        self.assertEqual(page.extraction_versions.count(), 1)
        self.assertGreater(page.extraction_versions.first().blocks.count(), 0)

    def test_txt_document_is_supported(self):
        document = self.make_txt()
        info = inspect_document(document.file.path)
        self.assertEqual(info["format"], "txt")
        run = process_document(document)
        self.assertEqual(run.status, "completed")
        page = Page.objects.get(document=document, is_current=True)
        self.assertIn("First paragraph", page.extracted_text)
        self.assertEqual(page.source_unit_label, "Text section 1")

    def test_reprocessing_preserves_prior_extraction_version(self):
        document = self.make_pdf()
        process_document(document)
        page = Page.objects.get(document=document, pdf_page_number=1)
        original_version_count = page.extraction_versions.count()
        process_document(document)
        page.refresh_from_db()
        self.assertEqual(page.extraction_versions.count(), original_version_count)
        self.assertTrue(page.is_current)

    def test_changed_document_creates_new_extraction_version(self):
        document = self.make_pdf()
        process_document(document)
        page = Page.objects.get(document=document, pdf_page_number=1)
        old_text = page.extracted_text
        path = Path(document.file.path)
        replacement = pymupdf.open()
        replacement.new_page().insert_text((72, 72), "Changed verified-looking sample")
        replacement.save(path)
        replacement.close()
        process_document(document)
        page.refresh_from_db()
        self.assertNotEqual(page.extracted_text, old_text)
        self.assertEqual(page.extraction_versions.count(), 2)

    def test_queue_worker_processes_document(self):
        document = self.make_txt()
        job = queue_document(document)
        self.assertEqual(job.status, "queued")
        processed = run_next_job()
        self.assertEqual(processed.pk, job.pk)
        self.assertEqual(processed.status, "completed")

    def test_duplicate_file_hash_is_rejected(self):
        first = self.make_txt("first.txt", "same content")
        second = self.make_txt("second.txt", "same content")
        process_document(first)
        run = process_document(second)
        self.assertEqual(run.status, "failed")
        self.assertIn("already exists", run.error_message)

