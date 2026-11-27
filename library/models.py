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
        ("hi", "Hindi"), ("fa", "Persian"), ("tr", "Turkish"),
        ("ota", "Ottoman Turkish"), ("bn", "Bengali"),
        ("id", "Indonesian"), ("ms", "Malay"), ("fr", "French"),
        ("de", "German"), ("ru", "Russian"),
        ("multi", "Multilingual"), ("und", "Unknown"),
    ]
    title = models.CharField(max_length=500, db_index=True)
    title_ar = models.CharField(max_length=500, blank=True)
    original_title = models.CharField(max_length=500, blank=True)
    transliterated_title = models.CharField(max_length=500, blank=True)
    alternate_titles = models.JSONField(default=list, blank=True)
    subtitle = models.CharField(max_length=500, blank=True)
    authors = models.ManyToManyField(Author, blank=True, related_name="books")
    categories = models.ManyToManyField("KnowledgeCategory", blank=True, related_name="books")
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
    publication_place = models.CharField(max_length=255, blank=True)
    editor = models.CharField(max_length=500, blank=True)
    translator = models.CharField(max_length=500, blank=True)
    series_title = models.CharField(max_length=255, blank=True)
    edition_statement = models.CharField(max_length=255, blank=True)
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


class KnowledgeCategory(models.Model):
    """Hierarchical subject taxonomy for Islamic scholarly works."""
    name = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(max_length=180, unique=True)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "knowledge categories"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.pk and self.parent_id == self.pk:
            raise ValidationError({"parent": "A category cannot be its own parent."})
        ancestor = self.parent
        seen = set()
        while ancestor is not None:
            if ancestor.pk in seen or (self.pk and ancestor.pk == self.pk):
                raise ValidationError({"parent": "Category hierarchy cannot contain a cycle."})
            seen.add(ancestor.pk)
            ancestor = ancestor.parent

    def __str__(self):
        return self.name


class SourceRecord(models.Model):
    """Provenance, access rights and verification details for a source."""
    SOURCE_TYPE = [
        ("publisher", "Publisher"), ("digital_library", "Digital library"),
        ("dataset", "Dataset"), ("manuscript_collection", "Manuscript collection"),
        ("institution", "Institution or archive"), ("website", "Website"),
        ("private_collection", "Private collection"), ("other", "Other"),
    ]
    RIGHTS_STATUS = [
        ("unknown", "Not yet determined"), ("public_domain", "Public domain"),
        ("open_license", "Open license"), ("permission_required", "Permission required"),
        ("restricted", "Restricted use"), ("proprietary", "Proprietary"),
    ]
    VERIFICATION_STATUS = [
        ("unverified", "Unverified"), ("verified", "Verified"),
        ("disputed", "Disputed"), ("rejected", "Rejected"),
    ]
    name = models.CharField(max_length=500, db_index=True)
    source_type = models.CharField(max_length=32, choices=SOURCE_TYPE, default="other")
    organization = models.CharField(max_length=255, blank=True)
    source_url = models.URLField(max_length=1000, blank=True)
    external_identifier = models.CharField(max_length=255, blank=True, db_index=True)
    license_name = models.CharField(max_length=255, blank=True)
    license_url = models.URLField(max_length=1000, blank=True)
    rights_status = models.CharField(max_length=24, choices=RIGHTS_STATUS, default="unknown")
    required_attribution = models.TextField(blank=True)
    accessed_at = models.DateField(null=True, blank=True)
    verification_status = models.CharField(max_length=16, choices=VERIFICATION_STATUS, default="unverified")
    verification_notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_source_records")
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


def upload_path(instance, filename):
    return f"library/documents/{instance.pk}/{filename}"


class SourceVerificationEvent(models.Model):
    """Append-only record of source verification and rights decisions."""
    source_record = models.ForeignKey(SourceRecord, on_delete=models.PROTECT, related_name="verification_events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    previous_status = models.CharField(max_length=16, blank=True)
    new_status = models.CharField(max_length=16)
    previous_rights_status = models.CharField(max_length=24, blank=True)
    new_rights_status = models.CharField(max_length=24)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"{self.source_record_id}: {self.new_status} / {self.new_rights_status}"


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
    source_record = models.ForeignKey(SourceRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    source_item_identifier = models.CharField(max_length=255, blank=True)
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
    engine_version = models.CharField(max_length=255, blank=True)
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
