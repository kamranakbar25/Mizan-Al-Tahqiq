import time

from django.core.management.base import BaseCommand

from library.services.universal_ingestion import run_next_job


class Command(BaseCommand):
    help = "Process queued document ingestion jobs."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Process at most one job and exit.")
        parser.add_argument("--poll-seconds", type=float, default=3.0)
        parser.add_argument("--max-jobs", type=int, default=0, help="0 means unlimited.")

    def handle(self, *args, **options):
        processed = 0
        poll_seconds = max(0.5, options["poll_seconds"])
        self.stdout.write(self.style.SUCCESS("Mizan ingestion worker started."))

        while True:
            job = run_next_job()
            if job is None:
                if options["once"]:
                    break
                time.sleep(poll_seconds)
                continue

            processed += 1
            self.stdout.write(
                f"Job {job.pk}: {job.status} "
                f"({job.progress_current}/{job.progress_total})"
            )

            if options["once"]:
                break
            if options["max_jobs"] and processed >= options["max_jobs"]:
                break

        self.stdout.write(self.style.SUCCESS(f"Worker finished. Jobs processed: {processed}"))
