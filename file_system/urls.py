from django.urls import path, include

from . import views

from rest_framework import routers
from file_system.views.file_group_view import FileGroupViewSet
from file_system.views.file_view import FileView, BatchPatchFiles, CopyFilesView
from file_system.views.manifest_view import Manifest
from file_system.views.storage_view import StorageViewSet
from file_system.views.file_metadata_view import FileMetadataView
from file_system.views.file_type_view import FileTypeView
from file_system.views.sample_view import SampleViewSet
from file_system.views.patient_view import PatientViewSet
from file_system.views.request_view import RequestViewSet
from file_system.views.distribution_view import DistributionView
from file_system.views.sample_view import SampleFullViewSet


router = routers.DefaultRouter()
router.register("storage", StorageViewSet)
router.register("file-groups", FileGroupViewSet)
router.register("file-types", FileTypeView)
router.register("files", FileView)
router.register("metadata", FileMetadataView)
router.register("sample", SampleViewSet)
router.register("request", RequestViewSet)
router.register("patient", PatientViewSet)
router.register("distribution", DistributionView)
router.register("project-details", SampleFullViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("batch-patch-files", BatchPatchFiles.as_view()),
    path("copy-files", CopyFilesView.as_view()),
    path("manifest/", Manifest.as_view()),
]
