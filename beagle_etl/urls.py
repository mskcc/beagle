from .views import JobViewSet
from rest_framework import routers
from django.urls import path, include
from beagle_etl.views import RequestIdLimsPullViewSet


router = routers.DefaultRouter()
router.register('jobs', JobViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('import-requests/', RequestIdLimsPullViewSet.as_view())
]