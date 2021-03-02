from .views import JobViewSet
from rest_framework import routers
from django.urls import path, include
from beagle_etl.views import RequestIdLimsPullViewSet, AssayViewSet, GetJobsTypes


router = routers.DefaultRouter()
router.register('jobs', JobViewSet)



urlpatterns = [
    path('', include(router.urls)),
    path('import-requests/', RequestIdLimsPullViewSet.as_view()),
    path('jobs-types',GetJobsTypes.as_view()),
    path('assay', AssayViewSet.as_view())
]