from django.shortcuts import render
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from library.models import (
    Author, Publisher, Book, Edition, Volume, Document, Page,
    IngestionRun, ProcessingJob,
)
from library.serializers import (
    AuthorSerializer, PublisherSerializer, BookSerializer, EditionSerializer,
    VolumeSerializer, DocumentSerializer, PageSerializer, IngestionRunSerializer,
    ProcessingJobSerializer,
)
from library.services.universal_ingestion import (
    inspect_document, queue_document,
)


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


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]


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
    queryset = Book.objects.prefetch_related("authors").all()
    serializer_class = BookSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "title_ar", "subtitle", "subject", "authors__name"]
    ordering_fields = ["title", "created_at"]


class EditionViewSet(BaseViewSet):
    queryset = Edition.objects.select_related("book", "publisher").all()
    serializer_class = EditionSerializer


class VolumeViewSet(BaseViewSet):
    queryset = Volume.objects.select_related("edition", "edition__book").all()
    serializer_class = VolumeSerializer


class DocumentViewSet(BaseViewSet):
    queryset = Document.objects.select_related("book", "edition", "volume").all()
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
    permission_classes = [IsAuthenticatedOrReadOnly]

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
