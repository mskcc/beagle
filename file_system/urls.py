from django.urls import path, include

from . import views

from rest_framework import routers
from file_system.views.file_group_view import FileGroupViewSet
from file_system.views.file_view import FileViewSet
from file_system.views.storage_view import StorageViewSet
from file_system.views.file_metadata_view import FileMetadataView
from file_system.views.sample_view import SampleView

router = routers.DefaultRouter()
router.register('storage', StorageViewSet)
router.register('file-group', FileGroupViewSet)
# router.register('files', FileViewSet)
router.register('metadata', FileMetadataView)
router.register('sample', SampleView)


urlpatterns = [
    path('', include(router.urls)),
    path('files/', FileViewSet.as_view())
]
