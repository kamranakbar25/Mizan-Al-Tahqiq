import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Author(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    name_ar = models.CharField(max_length=255, blank=True)
    biography = models.TextField(blank=True)
    birth_year = models.CharField(max_length=40, blank=True)
    death_year = models.CharField(max_length=40, blank=True)

    def __str__(self):
        return self.name


class Publisher(models.Model):
    name = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    LANGUAGE = [
        ("ar", "Arabic"), ("ur", "Urdu"), ("en", "English"),
        ("hi", "Hindi"), ("multi", "Multilingual"), ("und", "Unknown"),
    ]
    title = models.CharField(max_length=500, db_index=True)
    title_ar = models.CharField(max_length=500, blank=True)
    subtitle = models.CharField(max_length=500, blank=True)
    authors = models.ManyToManyField(Author, blank=True, related_name="books")
    language = models.CharField(max_length=8, choices=LANGUAGE, default="und")
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=120, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Edition(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="editions")
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True)
    edition_name = models.CharField(max_length=255, blank=True)
    publication_year = models.CharField(max_length=40, blank=True)
    isbn = models.CharField(max_length=40, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.book.title} — {self.edition_name or 'Edition unspecified'}"


class Volume(models.Model):
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE, related_name="volumes")
    volume_number = models.PositiveIntegerField()
    title = models.CharField(max_length=255, blank=True)
    printed_page_start = models.CharField(max_length=40, blank=True)
    printed_page_end = models.CharField(max_length=40, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["edition", "volume_number"], name="unique_volume_per_edition")
        ]
        ordering = ["volume_number"]

    def __str__(self):
        return f"{self.edition.book.title} — Volume {self.volume_number}"


def upload_path(instance, filename):
    return f"library/documents/{instance.pk}/{filename}"


class Document(models.Model):
    STATUS = [
        ("uploaded", "Uploaded"), ("inspected", "Inspected"),
        ("queued", "Queued"), ("processing", "Processing"),
        ("completed", "Completed"), ("partial", "Completed with issues"),
        ("failed", "Failed"),
    ]
    FORMAT = [
        ("pdf", "PDF"), ("txt", "Plain text"), ("docx", "Word DOCX"),
        ("epub", "EPUB"), ("image", "Image"), ("unknown", "Unknown"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="documents")
    edition = models.ForeignKey(Edition, on_delete=models.SET_NULL, null=True, blank=True)
    volume = models.ForeignKey(Volume, on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to=upload_path)
    original_filename = models.CharField(max_length=500)
    sha256 = models.CharField(max_length=64, blank=True, db_index=True)
    file_size = models.BigIntegerField(default=0)
    source_format = models.CharField(max_length=12, choices=FORMAT, default="unknown")
    detected_language = models.CharField(max_length=16, blank=True)
    pdf_page_count = models.PositiveIntegerField(null=True, blank=True)
    pdf_metadata = models.JSONField(default=dict, blank=True)
    processing_version = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS, default="uploaded")
    error_message = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.original_filename


class Page(models.Model):
    STATUS = [
        ("text_extracted", "Embedded text extracted"),
        ("ocr_required", "OCR required"),
        ("empty", "No text found"),
        ("error", "Extraction error"),
    ]
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="pages")
    pdf_page_index = models.PositiveIntegerField()
    pdf_page_number = models.PositiveIntegerField()
    printed_page_number = models.CharField(max_length=40, blank=True)
    source_unit_label = models.CharField(max_length=255, blank=True)
    is_current = models.BooleanField(default=True, db_index=True)
    width_points = models.FloatField(null=True, blank=True)
    height_points = models.FloatField(null=True, blank=True)
    rotation = models.IntegerField(default=0)
    extracted_text = models.TextField(blank=True)
    text_status = models.CharField(max_length=24, choices=STATUS)
    word_count = models.PositiveIntegerField(default=0)
    extraction_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["document", "pdf_page_index"], name="unique_page_per_document")
        ]
        ordering = ["document", "pdf_page_index"]
        indexes = [models.Index(fields=["text_status"])]

    def __str__(self):
        return f"{self.document.original_filename} — source unit {self.pdf_page_number}"


class IngestionRun(models.Model):
    STATUS = [("running", "Running"), ("completed", "Completed"),
              ("partial", "Completed with issues"), ("failed", "Failed")]
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="ingestion_runs")
    status = models.CharField(max_length=20, choices=STATUS, default="running")
    total_pages = models.PositiveIntegerField(default=0)
    processed_pages = models.PositiveIntegerField(default=0)
    text_pages = models.PositiveIntegerField(default=0)
    ocr_required_pages = models.PositiveIntegerField(default=0)
    error_pages = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    report = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)


class ProcessingJob(models.Model):
    STATUS = [
        ("queued", "Queued"), ("running", "Running"),
        ("completed", "Completed"), ("partial", "Completed with issues"),
        ("failed", "Failed"),
    ]
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="processing_jobs")
    status = models.CharField(max_length=16, choices=STATUS, default="queued", db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    progress_current = models.PositiveIntegerField(default=0)
    progress_total = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["status", "created_at"], name="lib_job_status_created_idx")]

    def __str__(self):
        return f"{self.document.original_filename} — {self.status}"


class ExtractionVersion(models.Model):
    SOURCE = [("embedded", "Embedded text"), ("ocr", "OCR"), ("manual", "Human corrected")]
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="extraction_versions")
    version_number = models.PositiveIntegerField()
    source = models.CharField(max_length=12, choices=SOURCE, default="embedded")
    engine_name = models.CharField(max_length=120, blank=True)
    engine_version = models.CharField(max_length=80, blank=True)
    text = models.TextField(blank=True)
    text_sha256 = models.CharField(max_length=64, blank=True)
    quality = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["page", "version_number"], name="unique_extraction_version_per_page")
        ]
        ordering = ["page", "version_number"]


class TextBlock(models.Model):
    TYPE = [
        ("paragraph", "Paragraph"), ("heading", "Heading"),
        ("footnote", "Footnote"), ("table", "Table"),
        ("other", "Other"),
    ]
    extraction = models.ForeignKey(ExtractionVersion, on_delete=models.CASCADE, related_name="blocks")
    order = models.PositiveIntegerField()
    block_type = models.CharField(max_length=16, choices=TYPE, default="paragraph")
    text = models.TextField()
    language = models.CharField(max_length=16, blank=True)
    bounding_box = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["extraction", "order"]
        constraints = [
            models.UniqueConstraint(fields=["extraction", "order"], name="unique_block_order_per_extraction")
        ]


class ReviewRecord(models.Model):
    STATUS = [("pending", "Pending"), ("approved", "Approved"),
              ("corrected", "Corrected"), ("rejected", "Rejected")]
    extraction = models.ForeignKey(ExtractionVersion, on_delete=models.CASCADE, related_name="reviews")
    status = models.CharField(max_length=12, choices=STATUS, default="pending")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    reviewed_text = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
