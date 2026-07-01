from rest_framework import routers
from django.urls import path, include
from beagle_etl.views import AssayViewSet, ForceImportView


router = routers.DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path("assay", AssayViewSet.as_view()),
    path("import/<str:request_id>/", ForceImportView.as_view()),
]
