from rest_framework import routers
from django.urls import path, include
from .views import JobGroupViews, JobGroupNotificationView, NotifierStartView, JiraStatusView


router = routers.DefaultRouter()
router.register('job-groups', JobGroupViews)


urlpatterns = [
    path('', include(router.urls)),
    path('send/', JobGroupNotificationView.as_view()),
    path('create/', NotifierStartView.as_view()),
    path('update/', JiraStatusView.as_view())
]

