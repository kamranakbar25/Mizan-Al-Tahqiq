from django.utils import timezone
from pathlib import Path
import zipfile
from rest_framework import serializers

from library.models import (
    Author, Publisher, Book, Edition, Volume, KnowledgeCategory, SourceRecord,
    SourceVerificationEvent, Document, Page, IngestionRun, ProcessingJob,
)


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = "__all__"


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = "__all__"


class KnowledgeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeCategory
        fields = "__all__"

    def validate_parent(self, parent):
        instance = self.instance
        if instance and parent and parent.pk == instance.pk:
            raise serializers.ValidationError("A category cannot be its own parent.")
        ancestor = parent
        visited = set()
        while ancestor is not None:
            if ancestor.pk in visited or (instance and ancestor.pk == instance.pk):
                raise serializers.ValidationError("Category hierarchy cannot contain a cycle.")
            visited.add(ancestor.pk)
            ancestor = ancestor.parent
        return parent


class SourceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceRecord
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "verified_at", "verified_by"]

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        is_staff = bool(user and user.is_authenticated and user.is_staff)
        instance = self.instance
        rights = attrs.get("rights_status", getattr(instance, "rights_status", "unknown"))
        verification = attrs.get("verification_status", getattr(instance, "verification_status", "unverified"))
        if not is_staff and rights != "unknown":
            raise serializers.ValidationError({"rights_status": "Only staff can change source rights status."})
        if not is_staff and verification != "unverified":
            raise serializers.ValidationError({"verification_status": "Only staff can verify or dispute a source."})
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_staff and validated_data.get("verification_status") == "verified":
            validated_data["verified_by"] = user
            validated_data["verified_at"] = timezone.now()
        created = super().create(validated_data)
        if user and user.is_staff and (created.verification_status != "unverified" or created.rights_status != "unknown"):
            SourceVerificationEvent.objects.create(
                source_record=created, actor=user, previous_status="",
                new_status=created.verification_status, previous_rights_status="",
                new_rights_status=created.rights_status, notes=created.verification_notes,
            )
        return created

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        old_status = instance.verification_status
        old_rights = instance.rights_status
        if user and user.is_staff:
            state = validated_data.get("verification_status", instance.verification_status)
            if state == "verified":
                validated_data["verified_by"] = user
                validated_data["verified_at"] = timezone.now()
            else:
                validated_data["verified_by"] = None
                validated_data["verified_at"] = None
        updated = super().update(instance, validated_data)
        if user and user.is_staff and (old_status != updated.verification_status or old_rights != updated.rights_status):
            SourceVerificationEvent.objects.create(
                source_record=updated, actor=user, previous_status=old_status,
                new_status=updated.verification_status, previous_rights_status=old_rights,
                new_rights_status=updated.rights_status, notes=updated.verification_notes,
            )
        return updated


class SourceVerificationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceVerificationEvent
        fields = "__all__"
        read_only_fields = fields


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
    MAX_UPLOAD_BYTES = 100 * 1024 * 1024
    ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".epub"}

    def validate_file(self, uploaded_file):
        extension = Path(uploaded_file.name).suffix.lower()
        if extension not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError("Supported formats: PDF, TXT, DOCX and EPUB.")
        if uploaded_file.size <= 0:
            raise serializers.ValidationError("The uploaded file is empty.")
        if uploaded_file.size > self.MAX_UPLOAD_BYTES:
            raise serializers.ValidationError("Maximum upload size is 100 MB.")
        head = uploaded_file.read(8192)
        uploaded_file.seek(0)
        if extension == ".pdf" and not head.lstrip().startswith(b"%PDF-"):
            raise serializers.ValidationError("File content is not a valid PDF signature.")
        if extension == ".txt":
            try:
                head.decode("utf-8-sig")
                if b"\x00" in head:
                    raise UnicodeError("NUL byte")
            except UnicodeError:
                raise serializers.ValidationError("TXT must contain valid UTF-8 text.")
        if extension in {".docx", ".epub"}:
            try:
                with zipfile.ZipFile(uploaded_file) as archive:
                    names = set(archive.namelist())
                    if len(names) > 10000 or sum(i.file_size for i in archive.infolist()) > 500 * 1024 * 1024:
                        raise serializers.ValidationError("Archive exceeds safe processing limits.")
                    if extension == ".docx" and not {"[Content_Types].xml", "word/document.xml"}.issubset(names):
                        raise serializers.ValidationError("DOCX package is missing required Word content.")
                    if extension == ".epub":
                        if "mimetype" not in names or archive.read("mimetype") != b"application/epub+zip":
                            raise serializers.ValidationError("EPUB package has an invalid mimetype.")
            except (zipfile.BadZipFile, KeyError, OSError):
                raise serializers.ValidationError("File is not a valid DOCX/EPUB package.")
            finally:
                uploaded_file.seek(0)
        return uploaded_file

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
