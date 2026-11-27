from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView

from library.models import (
    Author, Publisher, Book, Edition, Volume, KnowledgeCategory, SourceRecord,
    SourceVerificationEvent, Document, Page, IngestionRun, ProcessingJob,
)
from library.serializers import (
    AuthorSerializer, PublisherSerializer, BookSerializer, EditionSerializer,
    VolumeSerializer, KnowledgeCategorySerializer, SourceRecordSerializer,
    DocumentSerializer, PageSerializer, IngestionRunSerializer, ProcessingJobSerializer,
    SourceVerificationEventSerializer,
)
from library.services.universal_ingestion import (
    inspect_document, queue_document,
)


@login_required
def dashboard(request):
    return render(request, "library/dashboard.html", {
        "book_count": Book.objects.count(),
        "document_count": Document.objects.count(),
        "page_count": Page.objects.filter(is_current=True).count(),
        "ocr_required_count": Page.objects.filter(
            is_current=True, text_status="ocr_required"
        ).count(),
        "recent_documents": Document.objects.select_related("book").order_by("-uploaded_at")[:8],
    })


class ResearcherWriteStaffDelete(IsAuthenticated):
    """Authenticated researchers may work with records; only staff may delete."""
    def has_permission(self, request, view):
        allowed = super().has_permission(request, view)
        if not allowed:
            return False
        if getattr(view, "action", None) == "destroy":
            return bool(request.user and request.user.is_staff)
        return True


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [ResearcherWriteStaffDelete]


class AuthorViewSet(BaseViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "name_ar"]


class PublisherViewSet(BaseViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    search_fields = ["name"]


class BookViewSet(BaseViewSet):
    queryset = Book.objects.prefetch_related("authors", "categories").all()
    serializer_class = BookSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "title", "title_ar", "original_title", "transliterated_title",
        "subtitle", "subject", "authors__name", "authors__name_ar",
    ]
    ordering_fields = ["title", "created_at"]
    ordering = ["title", "pk"]

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get("category")
        language = self.request.query_params.get("language")
        if category:
            queryset = queryset.filter(categories__id=category)
        if language:
            queryset = queryset.filter(language=language)
        return queryset.distinct()


class KnowledgeCategoryViewSet(BaseViewSet):
    queryset = KnowledgeCategory.objects.select_related("parent").all()
    serializer_class = KnowledgeCategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["name", "sort_order"]
    ordering = ["sort_order", "name", "pk"]

    def get_queryset(self):
        queryset = super().get_queryset()
        parent = self.request.query_params.get("parent")
        if parent == "root":
            queryset = queryset.filter(parent__isnull=True)
        elif parent:
            queryset = queryset.filter(parent_id=parent)
        active = self.request.query_params.get("active")
        if active in {"true", "false"}:
            queryset = queryset.filter(is_active=(active == "true"))
        return queryset


class SourceRecordViewSet(BaseViewSet):
    queryset = SourceRecord.objects.select_related("verified_by").all()
    serializer_class = SourceRecordSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "organization", "external_identifier", "source_url"]
    ordering_fields = ["name", "created_at", "accessed_at", "verified_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        for parameter, field in (
            ("rights_status", "rights_status"),
            ("verification_status", "verification_status"),
            ("source_type", "source_type"),
        ):
            value = self.request.query_params.get(parameter)
            if value:
                queryset = queryset.filter(**{field: value})
        return queryset


class SourceVerificationEventViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = SourceVerificationEvent.objects.select_related("source_record", "actor").all()
    serializer_class = SourceVerificationEventSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        source_id = self.request.query_params.get("source_record")
        return queryset.filter(source_record_id=source_id) if source_id else queryset


class EditionViewSet(BaseViewSet):
    queryset = Edition.objects.select_related("book", "publisher").all()
    serializer_class = EditionSerializer


class VolumeViewSet(BaseViewSet):
    queryset = Volume.objects.select_related("edition", "edition__book").all()
    serializer_class = VolumeSerializer


class DocumentViewSet(BaseViewSet):
    queryset = Document.objects.select_related("book", "edition", "volume", "source_record").all()
    serializer_class = DocumentSerializer

    @action(detail=True, methods=["post"])
    def inspect(self, request, pk=None):
        document = self.get_object()
        try:
            result = inspect_document(document.file.path)
            document.source_format = result["format"]
            document.pdf_page_count = (
                result["unit_count"] if result["format"] == "pdf" else None
            )
            document.pdf_metadata = result.get("metadata", {})
            document.status = "inspected"
            document.save(update_fields=[
                "source_format", "pdf_page_count", "pdf_metadata", "status"
            ])
            return Response(result)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def ingest(self, request, pk=None):
        document = self.get_object()
        try:
            job = queue_document(document)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(ProcessingJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"])
    def pages(self, request, pk=None):
        queryset = self.get_object().pages.filter(is_current=True)
        state = request.query_params.get("status")
        if state:
            queryset = queryset.filter(text_status=state)
        return Response(PageSerializer(queryset, many=True).data)

    @action(detail=True, methods=["get"])
    def jobs(self, request, pk=None):
        jobs = self.get_object().processing_jobs.all()
        return Response(ProcessingJobSerializer(jobs, many=True).data)


class PageSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response(
                {"detail": "Provide q with at least 2 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pages = (
            Page.objects.filter(is_current=True, extracted_text__icontains=query)
            .select_related("document", "document__book")[:100]
        )
        rows = [{
            "book": page.document.book.title,
            "document_id": str(page.document_id),
            "source_unit": page.source_unit_label,
            "pdf_page_number": page.pdf_page_number,
            "text_status": page.text_status,
            "snippet": page.extracted_text[:700],
            "verification": "machine_extracted_unverified",
        } for page in pages]
        return Response({"query": query, "count": len(rows), "results": rows})
