from django.urls import path, include

from rest_framework import routers
from runner.views.run_view import RunViewSet, StartRunViewSet, UpdateJob
from runner.views.port_view import PortViewSet
from runner.views.run_api_view import RunApiViewSet, TempoOperatorViewSet, OperatorErrorViewSet
from runner.views.pipeline_view import PipelineViewSet, PipelineResolveViewSet, PipelineDownloadViewSet

router = routers.DefaultRouter()
router.register('pipelines', PipelineViewSet)
router.register('runs', RunViewSet)
router.register('port', PortViewSet)
router.register('api', RunApiViewSet)
router.register('operator-errors', OperatorErrorViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('pipeline/resolve/<uuid:pk>', PipelineResolveViewSet.as_view(), name='resolve-pipeline'),
    path('pipeline/download/<uuid:pk>', PipelineDownloadViewSet.as_view(), name='resolve-download'),
    path('run/start/<uuid:pk>', StartRunViewSet.as_view()),
    path('run/update/<uuid:pk>', UpdateJob.as_view()),
    path('request/', TempoOperatorViewSet.as_view())
]
