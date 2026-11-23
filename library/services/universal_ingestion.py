from __future__ import annotations

import hashlib
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path

import pymupdf
from django.db import transaction
from django.utils import timezone

from library.models import (
    Document, ExtractionVersion, IngestionRun, Page, ProcessingJob, TextBlock
)


SUPPORTED_FORMATS = {".pdf", ".txt", ".docx", ".epub"}


class UnsupportedDocumentError(ValueError):
    pass


class DuplicateDocumentError(ValueError):
    def __init__(self, existing_document):
        self.existing_document = existing_document
        super().__init__(
            f"This file already exists as document {existing_document.pk} "
            f"({existing_document.original_filename})."
        )


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _format_for(path: Path) -> str:
    suffix = path.suffix.lower()
    mapping = {".pdf": "pdf", ".txt": "txt", ".docx": "docx", ".epub": "epub"}
    return mapping.get(suffix, "unknown")


def inspect_document(path: str | Path) -> dict:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise UnsupportedDocumentError(
            f"Unsupported format '{suffix or 'no extension'}'. "
            f"Supported in v1: PDF, TXT, DOCX and EPUB."
        )

    if suffix == ".pdf":
        with pymupdf.open(path) as doc:
            if doc.is_encrypted:
                raise ValueError("Encrypted PDFs are not supported.")
            return {
                "format": "pdf",
                "unit_count": doc.page_count,
                "metadata": {str(k): str(v or "") for k, v in (doc.metadata or {}).items()},
                "encrypted": False,
            }

    if suffix == ".txt":
        text = _read_text(path)
        units = text.split("\f") or [text]
        return {"format": "txt", "unit_count": max(1, len(units)), "metadata": {}}

    if suffix == ".docx":
        from docx import Document as DocxDocument
        doc = DocxDocument(path)
        return {"format": "docx", "unit_count": 1, "metadata": {
            "paragraph_count": len(doc.paragraphs), "table_count": len(doc.tables)
        }}

    with zipfile.ZipFile(path) as archive:
        html_files = sorted(
            n for n in archive.namelist()
            if n.lower().endswith((".xhtml", ".html", ".htm"))
        )
        if not html_files:
            raise ValueError("EPUB contains no HTML/XHTML content documents.")
        return {"format": "epub", "unit_count": len(html_files), "metadata": {
            "html_document_count": len(html_files)
        }}


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1256", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


class _TextHTMLParser(HTMLParser):
    BLOCK_TAGS = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "tr"}

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        cleaned = data.strip()
        if cleaned:
            self.parts.append(cleaned)

    def text(self):
        return re.sub(r"[ \t]+\n", "\n", re.sub(r"\n{3,}", "\n\n", " ".join(self.parts))).strip()


def _units_from_file(path: Path):
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        with pymupdf.open(path) as doc:
            if doc.is_encrypted:
                raise ValueError("Encrypted PDFs are not supported.")
            metadata = {str(k): str(v or "") for k, v in (doc.metadata or {}).items()}
            for index, page in enumerate(doc):
                text = page.get_text("text", sort=True).strip()
                yield {
                    "index": index, "label": f"PDF page {index + 1}",
                    "text": text, "width": page.rect.width,
                    "height": page.rect.height, "rotation": page.rotation,
                    "status": "text_extracted" if text else "ocr_required",
                    "metadata": metadata,
                }
        return

    if suffix == ".txt":
        text = _read_text(path)
        for index, part in enumerate(text.split("\f") or [text]):
            cleaned = part.strip()
            yield {
                "index": index, "label": f"Text section {index + 1}",
                "text": cleaned, "status": "text_extracted" if cleaned else "empty",
                "metadata": {},
            }
        return

    if suffix == ".docx":
        from docx import Document as DocxDocument
        doc = DocxDocument(path)
        parts = []
        for paragraph in doc.paragraphs:
            value = paragraph.text.strip()
            if value:
                parts.append(value)
        for table_index, table in enumerate(doc.tables, start=1):
            rows = []
            for row in table.rows:
                rows.append(" | ".join(cell.text.strip() for cell in row.cells))
            parts.append(f"[Table {table_index}]\n" + "\n".join(rows))
        text = "\n\n".join(parts).strip()
        yield {
            "index": 0, "label": "DOCX document",
            "text": text, "status": "text_extracted" if text else "empty",
            "metadata": {"paragraph_count": len(doc.paragraphs), "table_count": len(doc.tables)},
        }
        return

    if suffix == ".epub":
        with zipfile.ZipFile(path) as archive:
            names = sorted(
                n for n in archive.namelist()
                if n.lower().endswith((".xhtml", ".html", ".htm"))
            )
            for index, name in enumerate(names):
                parser = _TextHTMLParser()
                parser.feed(archive.read(name).decode("utf-8", errors="replace"))
                text = parser.text()
                yield {
                    "index": index, "label": f"EPUB item: {name}",
                    "text": text, "status": "text_extracted" if text else "empty",
                    "metadata": {"epub_item": name},
                }
        return

    raise UnsupportedDocumentError(f"Unsupported document format: {suffix}")


def _store_extraction(page: Page, text: str, source: str = "embedded", engine: str = "native-extractor"):
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    latest = page.extraction_versions.order_by("-version_number").first()
    if latest and latest.text_sha256 == digest and latest.source == source:
        return latest, False

    version_number = (latest.version_number + 1) if latest else 1
    extraction = ExtractionVersion.objects.create(
        page=page,
        version_number=version_number,
        source=source,
        engine_name=engine,
        text=text,
        text_sha256=digest,
        quality={
            "character_count": len(text),
            "word_count": len(text.split()),
            "automatically_verified": False,
        },
    )

    blocks = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    TextBlock.objects.bulk_create([
        TextBlock(extraction=extraction, order=i, block_type="paragraph", text=block)
        for i, block in enumerate(blocks)
    ])
    return extraction, True


def process_document(document: Document, job: ProcessingJob | None = None) -> IngestionRun:
    path = Path(document.file.path)
    run = IngestionRun.objects.create(document=document, status="running")
    document.status = "processing"
    document.error_message = ""
    document.save(update_fields=["status", "error_message"])

    try:
        file_hash = sha256_file(path)
        duplicate = Document.objects.filter(sha256=file_hash).exclude(pk=document.pk).first()
        if duplicate:
            raise DuplicateDocumentError(duplicate)

        info = inspect_document(path)
        document.sha256 = file_hash
        document.source_format = info["format"]
        document.pdf_metadata = info.get("metadata", {})
        document.pdf_page_count = info["unit_count"] if info["format"] == "pdf" else None
        document.processing_version += 1
        document.save(update_fields=[
            "sha256", "source_format", "pdf_metadata", "pdf_page_count", "processing_version"
        ])

        run.total_pages = info["unit_count"]
        run.save(update_fields=["total_pages"])

        for unit in _units_from_file(path):
            with transaction.atomic():
                page, _ = Page.objects.update_or_create(
                    document=document,
                    pdf_page_index=unit["index"],
                    defaults={
                        "pdf_page_number": unit["index"] + 1,
                        "source_unit_label": unit["label"],
                        "width_points": unit.get("width"),
                        "height_points": unit.get("height"),
                        "rotation": unit.get("rotation", 0),
                        "extracted_text": unit["text"],
                        "text_status": unit["status"],
                        "word_count": len(unit["text"].split()),
                        "extraction_error": "",
                        "is_current": True,
                    },
                )
                if unit["text"]:
                    _store_extraction(page, unit["text"])
                    run.text_pages += 1
                elif unit["status"] == "ocr_required":
                    run.ocr_required_pages += 1
                else:
                    run.error_pages += 1

                run.processed_pages += 1
                run.save(update_fields=[
                    "processed_pages", "text_pages", "ocr_required_pages", "error_pages"
                ])
                if job:
                    ProcessingJob.objects.filter(pk=job.pk).update(
                        progress_current=run.processed_pages,
                        progress_total=run.total_pages,
                    )

        # Keep prior page rows and extraction versions. Only after a complete
        # pass mark obsolete trailing units as non-current; never delete them.
        Page.objects.filter(document=document, pdf_page_index__gte=run.total_pages).update(is_current=False)
        if run.error_pages:
            final_status = "partial"
        elif run.ocr_required_pages:
            final_status = "partial"
        else:
            final_status = "completed"

        run.status = final_status
        run.report = {
            "sha256": file_hash,
            "format": info["format"],
            "units": run.total_pages,
            "text_units": run.text_pages,
            "ocr_required_units": run.ocr_required_pages,
            "empty_or_error_units": run.error_pages,
            "processing_version": document.processing_version,
            "note": "Extraction is machine-generated and has not been religiously or textually verified.",
        }
        document.status = final_status
        document.processed_at = timezone.now()
        document.save(update_fields=["status", "processed_at"])
        if job:
            job.status = final_status
            job.result = run.report
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "result", "finished_at"])
    except Exception as exc:
        run.status = "failed"
        run.error_message = f"{type(exc).__name__}: {exc}"
        document.status = "failed"
        document.error_message = run.error_message
        document.save(update_fields=["status", "error_message"])
        if job:
            job.status = "failed"
            job.error_message = run.error_message
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "error_message", "finished_at"])
    finally:
        run.finished_at = timezone.now()
        run.save()

    return run


def queue_document(document: Document) -> ProcessingJob:
    if ProcessingJob.objects.filter(document=document, status__in=["queued", "running"]).exists():
        raise ValueError("This document already has a queued or running processing job.")
    job = ProcessingJob.objects.create(document=document, status="queued")
    document.status = "queued"
    document.save(update_fields=["status"])
    return job


def run_next_job() -> ProcessingJob | None:
    # Conditional update is a lightweight claim operation that prevents two
    # workers from claiming the same queued job at the same time.
    candidate = ProcessingJob.objects.filter(status="queued").order_by("created_at").first()
    if not candidate:
        return None
    claimed = ProcessingJob.objects.filter(pk=candidate.pk, status="queued").update(
        status="running", attempts=candidate.attempts + 1, started_at=timezone.now()
    )
    if not claimed:
        return None
    candidate.refresh_from_db()
    process_document(candidate.document, candidate)
    candidate.refresh_from_db()
    return candidate
