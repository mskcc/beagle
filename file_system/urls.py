from django.urls import path, include

from . import views

from rest_framework import routers
from file_system.views.cohort_view import CohortViewSet
from file_system.views.file_view import FileViewSet
from file_system.views.storage_view import StorageViewSet
from file_system.views.file_metadata_view import FileMetadataView

router = routers.DefaultRouter()
router.register('storage', StorageViewSet)
router.register('cohort', CohortViewSet)
router.register('files', FileViewSet)
router.register('metadata', FileMetadataView)


urlpatterns = [
    path('', include(router.urls)),
]
