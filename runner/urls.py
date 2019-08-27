from django.urls import path, include

from . import views

from rest_framework import routers
from django.conf.urls import url
from runner.views.pipeline_view import PipelineViewSet, PipelineResolveViewSet, PipelineDownloadViewSet

router = routers.DefaultRouter()
router.register('pipelines', PipelineViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('pipeline/resolve/<uuid:pk>', PipelineResolveViewSet.as_view(), name='resolve-pipeline'),
    path('pipeline/download/<uuid:pk>', PipelineDownloadViewSet.as_view(), name='resolve-download')
]
