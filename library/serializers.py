from rest_framework import serializers

from library.models import (
    Author, Publisher, Book, Edition, Volume, Document, Page,
    IngestionRun, ProcessingJob,
)


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = "__all__"


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = "__all__"


class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True, read_only=True)
    author_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Author.objects.all(), source="authors",
        write_only=True, required=False,
    )

    class Meta:
        model = Book
        fields = "__all__"


class EditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edition
        fields = "__all__"


class VolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Volume
        fields = "__all__"


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"
        read_only_fields = [
            "id", "original_filename", "sha256", "file_size",
            "pdf_page_count", "pdf_metadata", "source_format",
            "detected_language", "processing_version", "status",
            "error_message", "uploaded_at", "processed_at",
        ]

    def create(self, validated_data):
        uploaded_file = validated_data["file"]
        validated_data["original_filename"] = uploaded_file.name
        validated_data["file_size"] = uploaded_file.size
        return super().create(validated_data)


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = "__all__"


class IngestionRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionRun
        fields = "__all__"


class ProcessingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingJob
        fields = "__all__"
