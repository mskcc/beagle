from rest_framework import routers
from django.urls import path, include
from operator_manager.views import OperatorViewSet


router = routers.DefaultRouter()
router.register("operators", OperatorViewSet)


urlpatterns = [
    path("", include(router.urls)),
]
