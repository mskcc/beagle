from .views import JobViewSet
from rest_framework import routers
from django.urls import path, include
from beagle_etl.views import RequestIdLimsPullViewSet, AssayViewSet, GetJobsTypes


router = routers.DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path("assay", AssayViewSet.as_view()),
]
