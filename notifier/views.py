import logging
from rest_framework import mixins
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import GenericAPIView

from .tasks import send_notification
from .models import JobGroup
from .serializers import JobGroupSerializer, NotificationSerializer


class JobGroupViews(mixins.CreateModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.ListModelMixin,
                    GenericViewSet):

    queryset = JobGroup.objects.all()
    serializer_class = JobGroupSerializer


class JobGroupNotificationView(GenericAPIView):
    logger = logging.getLogger(__name__)

    serializer_class = NotificationSerializer

    def post(self, request):
        job_group = request.data['job_group']
        try:
            JobGroup.objects.get(id=job_group)
        except JobGroup.DoesNotExist:
            return Response({"details": "JobGroup %s Not Found" % job_group},
                            status=status.HTTP_400_BAD_REQUEST)
        notification = request.data['notification']
        event = request.data['arguments']
        event['job_group'] = job_group
        event['class'] = notification
        send_notification.delay(event)
        return Response({"details": "Event sent %s" % str(event)},
                        status=status.HTTP_201_CREATED)
