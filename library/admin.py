from django.contrib import admin

from library.models import (
    Author, Publisher, Book, Edition, Volume, Document, Page,
    IngestionRun, ProcessingJob, ExtractionVersion, TextBlock, ReviewRecord,
)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    search_fields = ["name", "name_ar"]
    list_display = ["name", "birth_year", "death_year"]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    search_fields = ["title", "title_ar"]
    list_display = ["title", "language", "subject"]
    filter_horizontal = ["authors"]


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    search_fields = ["name"]


class VolumeInline(admin.TabularInline):
    model = Volume
    extra = 0


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = ["book", "edition_name", "publisher", "publication_year"]
    inlines = [VolumeInline]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "original_filename", "book", "source_format", "status",
        "pdf_page_count", "processing_version", "uploaded_at",
    ]
    list_filter = ["status", "source_format"]
    search_fields = ["original_filename", "book__title", "sha256"]
    readonly_fields = [
        "sha256", "file_size", "pdf_page_count", "pdf_metadata",
        "uploaded_at", "processed_at", "processing_version",
    ]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = [
        "document", "pdf_page_number", "source_unit_label",
        "text_status", "is_current", "word_count",
    ]
    list_filter = ["text_status", "is_current"]
    search_fields = ["extracted_text", "source_unit_label"]


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    list_display = [
        "document", "status", "total_pages", "processed_pages",
        "started_at", "finished_at",
    ]
    readonly_fields = [field.name for field in IngestionRun._meta.fields]


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = [
        "document", "status", "attempts", "progress_current",
        "progress_total", "created_at",
    ]
    list_filter = ["status"]
    readonly_fields = [field.name for field in ProcessingJob._meta.fields]


@admin.register(ExtractionVersion)
class ExtractionVersionAdmin(admin.ModelAdmin):
    list_display = ["page", "version_number", "source", "engine_name", "created_at"]
    list_filter = ["source", "engine_name"]
    search_fields = ["text", "text_sha256"]


@admin.register(TextBlock)
class TextBlockAdmin(admin.ModelAdmin):
    list_display = ["extraction", "order", "block_type", "language"]
    search_fields = ["text"]


@admin.register(ReviewRecord)
class ReviewRecordAdmin(admin.ModelAdmin):
    list_display = ["extraction", "status", "reviewer", "reviewed_at"]
    list_filter = ["status"]


admin.site.site_header = "Mizan al-Tahqiq Administration"
admin.site.site_title = "Mizan al-Tahqiq"
admin.site.index_title = "Digital Islamic Research Library"
