from .views import JobGroupViews, JobGroupNotificationView, NotifierStartView
from rest_framework import routers
from django.urls import path, include


router = routers.DefaultRouter()
router.register('job-groups', JobGroupViews)


urlpatterns = [
    path('', include(router.urls)),
    path('send/', JobGroupNotificationView.as_view()),
    path('create/', NotifierStartView.as_view())
]

