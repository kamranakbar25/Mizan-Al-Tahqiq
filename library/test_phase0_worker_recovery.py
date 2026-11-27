from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from library.models import Book, Document, ProcessingJob
from library.services.universal_ingestion import run_next_job


class WorkerStaleRecoveryTests(TestCase):
    def setUp(self):
        book = Book.objects.create(title="Worker recovery test book")
        self.document = Document.objects.create(
            book=book,
            original_filename="worker-recovery.txt",
            status="processing",
        )

    def make_stale_job(self, attempts):
        return ProcessingJob.objects.create(
            document=self.document,
            status="running",
            attempts=attempts,
            started_at=timezone.now() - timedelta(minutes=31),
        )

    @patch("library.services.universal_ingestion.process_document")
    def test_stale_job_below_attempt_limit_is_requeued_and_claimed(self, process):
        job = self.make_stale_job(attempts=1)

        result = run_next_job()

        job.refresh_from_db()
        self.assertEqual(result.pk, job.pk)
        self.assertEqual(job.status, "running")
        self.assertEqual(job.attempts, 2)
        self.assertIsNotNone(job.started_at)
        process.assert_called_once()

    @patch("library.services.universal_ingestion.process_document")
    def test_stale_job_at_attempt_limit_becomes_terminal_failure(self, process):
        job = self.make_stale_job(attempts=3)

        result = run_next_job()

        job.refresh_from_db()
        self.document.refresh_from_db()
        self.assertIsNone(result)
        self.assertEqual(job.status, "failed")
        self.assertIsNotNone(job.finished_at)
        self.assertIn("maximum attempts", job.error_message)
        self.assertEqual(self.document.status, "failed")
        process.assert_not_called()
