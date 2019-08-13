from django.urls import path, include

from . import views

from rest_framework import routers
from django.conf.urls import url
from runner.views.pipeline_view import PipelineViewSet

router = routers.DefaultRouter()

urlpatterns = [
    #path('', include(router.urls)),
    path('pipeline/<uuid:pk>', PipelineViewSet.as_view(), name='resolve-pipeline')
]
