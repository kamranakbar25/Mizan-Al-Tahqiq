# Generated for Mizan al-Tahqiq Universal Ingestion v1.
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="document", name="source_format",
            field=models.CharField(
                choices=[("pdf", "PDF"), ("txt", "Plain text"), ("docx", "Word DOCX"),
                         ("epub", "EPUB"), ("image", "Image"), ("unknown", "Unknown")],
                default="unknown", max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="document", name="detected_language",
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name="document", name="processing_version",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="document", name="status",
            field=models.CharField(
                choices=[("uploaded", "Uploaded"), ("inspected", "Inspected"),
                         ("queued", "Queued"), ("processing", "Processing"),
                         ("completed", "Completed"), ("partial", "Completed with issues"),
                         ("failed", "Failed")],
                default="uploaded", max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="page", name="source_unit_label",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="page", name="is_current",
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name="ingestionrun", name="status",
            field=models.CharField(
                choices=[("running", "Running"), ("completed", "Completed"),
                         ("partial", "Completed with issues"), ("failed", "Failed")],
                default="running", max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="ProcessingJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(
                    choices=[("queued", "Queued"), ("running", "Running"),
                             ("completed", "Completed"), ("partial", "Completed with issues"),
                             ("failed", "Failed")],
                    db_index=True, default="queued", max_length=16,
                )),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("progress_current", models.PositiveIntegerField(default=0)),
                ("progress_total", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("result", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                               related_name="processing_jobs", to="library.document")),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddIndex(
            model_name="processingjob",
            index=models.Index(fields=["status", "created_at"], name="lib_job_status_created_idx"),
        ),
        migrations.CreateModel(
            name="ExtractionVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version_number", models.PositiveIntegerField()),
                ("source", models.CharField(
                    choices=[("embedded", "Embedded text"), ("ocr", "OCR"), ("manual", "Human corrected")],
                    default="embedded", max_length=12,
                )),
                ("engine_name", models.CharField(blank=True, max_length=120)),
                ("engine_version", models.CharField(blank=True, max_length=80)),
                ("text", models.TextField(blank=True)),
                ("text_sha256", models.CharField(blank=True, max_length=64)),
                ("quality", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("page", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="extraction_versions", to="library.page")),
            ],
            options={"ordering": ["page", "version_number"]},
        ),
        migrations.AddConstraint(
            model_name="extractionversion",
            constraint=models.UniqueConstraint(fields=("page", "version_number"),
                                                name="unique_extraction_version_per_page"),
        ),
        migrations.CreateModel(
            name="TextBlock",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveIntegerField()),
                ("block_type", models.CharField(
                    choices=[("paragraph", "Paragraph"), ("heading", "Heading"),
                             ("footnote", "Footnote"), ("table", "Table"), ("other", "Other")],
                    default="paragraph", max_length=16,
                )),
                ("text", models.TextField()),
                ("language", models.CharField(blank=True, max_length=16)),
                ("bounding_box", models.JSONField(blank=True, default=dict)),
                ("extraction", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                 related_name="blocks", to="library.extractionversion")),
            ],
            options={"ordering": ["extraction", "order"]},
        ),
        migrations.AddConstraint(
            model_name="textblock",
            constraint=models.UniqueConstraint(fields=("extraction", "order"),
                                                name="unique_block_order_per_extraction"),
        ),
        migrations.CreateModel(
            name="ReviewRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(
                    choices=[("pending", "Pending"), ("approved", "Approved"),
                             ("corrected", "Corrected"), ("rejected", "Rejected")],
                    default="pending", max_length=12,
                )),
                ("notes", models.TextField(blank=True)),
                ("reviewed_text", models.TextField(blank=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("extraction", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                 related_name="reviews", to="library.extractionversion")),
                ("reviewer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                               to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
