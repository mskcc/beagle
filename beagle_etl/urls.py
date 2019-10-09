from .views import JobViewSet
from rest_framework import routers
from django.urls import path, include


router = routers.DefaultRouter()
router.register('jobs', JobViewSet)


urlpatterns = [
    path('', include(router.urls)),
]