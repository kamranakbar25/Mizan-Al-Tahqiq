from django.test import TestCase
from library.models import Book, Document, Edition, KnowledgeCategory, SourceRecord


class ScholarlyMetadataFoundationTests(TestCase):
    def test_book_supports_original_and_transliterated_titles(self):
        book = Book.objects.create(title="The Book", original_title="كتاب", transliterated_title="Kitab", alternate_titles=["Al-Kitab"], language="ar")
        self.assertEqual(book.original_title, "كتاب")
        self.assertEqual(book.transliterated_title, "Kitab")
        self.assertEqual(book.alternate_titles, ["Al-Kitab"])

    def test_book_can_have_hierarchical_scholarly_categories(self):
        parent = KnowledgeCategory.objects.create(name="Hadith", slug="hadith")
        child = KnowledgeCategory.objects.create(name="Hadith Sciences", slug="hadith-sciences", parent=parent)
        book = Book.objects.create(title="A Hadith work")
        book.categories.add(parent, child)
        self.assertEqual(book.categories.count(), 2)
        self.assertEqual(child.parent, parent)

    def test_source_registry_defaults_to_unverified_and_unknown_rights(self):
        source = SourceRecord.objects.create(name="Example Digital Collection", source_type="digital_library")
        self.assertEqual(source.rights_status, "unknown")
        self.assertEqual(source.verification_status, "unverified")

    def test_document_can_link_to_source_record(self):
        book = Book.objects.create(title="A sourced work")
        source = SourceRecord.objects.create(name="Archive")
        document = Document.objects.create(book=book, source_record=source, original_filename="source.pdf")
        self.assertEqual(document.source_record, source)

    def test_edition_has_editor_translator_and_publication_place(self):
        book = Book.objects.create(title="Edited work")
        edition = Edition.objects.create(book=book, editor="Editor Name", translator="Translator Name", publication_place="Beirut")
        self.assertEqual(edition.editor, "Editor Name")
        self.assertEqual(edition.translator, "Translator Name")
        self.assertEqual(edition.publication_place, "Beirut")
