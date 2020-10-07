from django.urls import path, include

from . import views

from rest_framework import routers
from file_system.views.file_group_view import FileGroupViewSet
from file_system.views.file_view import FileView, BatchPatchFiles
from file_system.views.storage_view import StorageViewSet
from file_system.views.file_metadata_view import FileMetadataView
from file_system.views.file_type_view import FileTypeView


router = routers.DefaultRouter()
router.register('storage', StorageViewSet)
router.register('file-groups', FileGroupViewSet)
router.register('file-types', FileTypeView)
router.register('files', FileView)
router.register('metadata', FileMetadataView)


urlpatterns = [
    path('', include(router.urls)),
    path('batch-patch-files', BatchPatchFiles.as_view())
]
