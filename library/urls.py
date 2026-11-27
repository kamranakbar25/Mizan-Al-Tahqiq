from django.urls import path,include
from rest_framework.routers import DefaultRouter
from library.views import (
    AuthorViewSet, PublisherViewSet, BookViewSet, EditionViewSet, VolumeViewSet,
    KnowledgeCategoryViewSet, SourceRecordViewSet, SourceVerificationEventViewSet, DocumentViewSet, PageSearchView,
)
router=DefaultRouter()
for prefix, view, name in [
    ("authors", AuthorViewSet, "author"),
    ("publishers", PublisherViewSet, "publisher"),
    ("books", BookViewSet, "book"),
    ("editions", EditionViewSet, "edition"),
    ("volumes", VolumeViewSet, "volume"),
    ("categories", KnowledgeCategoryViewSet, "category"),
    ("sources", SourceRecordViewSet, "source"),
    ("source-verification-events", SourceVerificationEventViewSet, "source-verification-event"),
    ("documents", DocumentViewSet, "document"),
]:
    router.register(prefix, view, basename=name)
urlpatterns=[path("",include(router.urls)),path("search/pages/",PageSearchView.as_view(),name="page-search")]
