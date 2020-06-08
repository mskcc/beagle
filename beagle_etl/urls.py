from .views import JobViewSet
from rest_framework import routers
from django.urls import path, include
from beagle_etl.views import RequestIdLimsPullViewSet, RequestIdLimsUpdateViewSet, AssayViewSet


router = routers.DefaultRouter()
router.register('jobs', JobViewSet)
router.register('assay', AssayViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('import-requests/', RequestIdLimsPullViewSet.as_view()),
    path('update-requests/', RequestIdLimsUpdateViewSet.as_view())
]