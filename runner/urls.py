from django.urls import path, include

from rest_framework import routers
from runner.views.run_view import RunViewSet, StartRunViewSet, UpdateJob
from runner.views.port_view import PortViewSet
from runner.views.operator_run_view import OperatorRunViewSet
from runner.views.run_api_view import RunApiViewSet, OperatorViewSet, OperatorErrorViewSet, RequestOperatorViewSet, \
    RunOperatorViewSet, AionViewSet, TempoMPGenViewSet, CWLJsonViewSet, PairsOperatorViewSet, RunApiRestartViewSet, \
    RunSamplesViewSet, OperatorSamplesLatestViewSet, OperatorSamplesAllViewSet
from runner.views.pipeline_view import PipelineViewSet, PipelineResolveViewSet, PipelineDownloadViewSet


router = routers.DefaultRouter()
router.register('pipelines', PipelineViewSet)
router.register('runs', RunViewSet)
router.register('samples', RunSamplesViewSet)
router.register('port', PortViewSet)
router.register('api', RunApiViewSet)
router.register('operator/latest', OperatorSamplesLatestViewSet)
router.register('operator/all', OperatorSamplesAllViewSet)
router.register('operator-errors', OperatorErrorViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('pipeline/resolve/<uuid:pk>', PipelineResolveViewSet.as_view(), name='resolve-pipeline'),
    path('pipeline/download/<uuid:pk>', PipelineDownloadViewSet.as_view(), name='resolve-download'),
    path('run/start/<uuid:pk>', StartRunViewSet.as_view()),
    path('run/update/<uuid:pk>', UpdateJob.as_view()),
    path('restart/', RunApiRestartViewSet.as_view()),
    path('request/', OperatorViewSet.as_view()),
    path('operator-runs/', OperatorRunViewSet.as_view({'get': 'list'})),
    path('operator/request/', RequestOperatorViewSet.as_view()),
    path('operator/runs/', RunOperatorViewSet.as_view()),
    path('operator/pairs/', PairsOperatorViewSet.as_view()),
    path('operator/aion/', AionViewSet.as_view()),
    path('operator/tempo_mpgen/', TempoMPGenViewSet.as_view()),
    path('cwljson/', CWLJsonViewSet.as_view())
]
