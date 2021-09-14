from rest_framework import routers
from django.urls import path, include
from .views import JobGroupViews, JobGroupNotificationView, NotifierStartView, JiraStatusView, ProjectStatusView


router = routers.DefaultRouter()
router.register('job-groups', JobGroupViews)
router.register('status-page', ProjectStatusView)


urlpatterns = [
    path('', include(router.urls)),
    path('send/', JobGroupNotificationView.as_view()),
    path('create/', NotifierStartView.as_view()),
    path('update/', JiraStatusView.as_view()),
]

