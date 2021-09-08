import logging
from rest_framework import mixins
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import GenericAPIView
from drf_yasg.utils import swagger_auto_schema
from .tasks import send_notification, notifier_start
from .models import JobGroup, JobGroupNotifier, JiraStatus
from runner.models import Pipeline
from .serializers import JobGroupSerializer, NotificationSerializer, JobGroupQuerySerializer, CreateNotifierSerializer, \
    JiraStatusSerializer


class JobGroupViews(mixins.CreateModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.ListModelMixin,
                    GenericViewSet):

    queryset = JobGroup.objects.all()
    serializer_class = JobGroupSerializer

    @swagger_auto_schema(query_serializer=JobGroupQuerySerializer)
    def list(self, request, *args, **kwargs):
        job_groups = JobGroup.objects.all()
        serializer = JobGroupQuerySerializer(data=request.query_params)
        if serializer.is_valid():
            jira_id = request.query_params.get('jira_id')
            if jira_id:
                job_groups = JobGroup.objects.filter(jira_id=jira_id).all()
        else:
            Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        page = self.paginate_queryset(job_groups)
        response = JobGroupSerializer(page, many=True)
        return self.get_paginated_response(response.data)


class JobGroupNotificationView(GenericAPIView):
    logger = logging.getLogger(__name__)

    serializer_class = NotificationSerializer

    def post(self, request):
        job_notifier = request.data['job_notifier']
        try:
            JobGroupNotifier.objects.get(id=job_notifier)
        except JobGroupNotifier.DoesNotExist:
            return Response({"details": "JobGroupNotifier %s Not Found" % job_notifier},
                            status=status.HTTP_400_BAD_REQUEST)
        notification = request.data['notification']
        event = request.data['arguments']
        event['job_notifier'] = job_notifier
        event['class'] = notification
        send_notification.delay(event)
        return Response({"details": "Event sent %s" % str(event)},
                        status=status.HTTP_201_CREATED)


class NotifierStartView(GenericAPIView):
    logger = logging.getLogger(__name__)

    serializer_class = CreateNotifierSerializer

    def post(self, request):
        job_group = request.data['job_group']
        try:
            JobGroup.objects.get(id=job_group)
        except JobGroup.DoesNotExist:
            return Response({"details": "JobGroup %s Not Found" % job_group},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            pipeline = Pipeline.get(name=request.data.get('pipeline'))
        except Pipeline.DoesNotExist:
            pipeline = None

        request_id = request.data['job_group']
        notifier_id = notifier_start(job_group, request_id, pipeline.operator)
        return Response({"notifier_id": notifier_id}, status=status.HTTP_201_CREATED)


class JiraStatusView(GenericAPIView):

    serializer_class = JiraStatusSerializer
    permission_classes = []

    def _convert_to_status(self, status):
        if status == 'Ready For Standard Delivery':
            return JiraStatus.READY_FOR_STANDARD_DELIVERY
        elif status == 'Ready For Custom Delivery':
            return JiraStatus.READY_FOR_CUSTOM_DELIVERY
        elif status == 'Not for CI':
            return JiraStatus.NOT_FOR_CI
        elif status == "Can't Do":
            return JiraStatus.CANT_DO
        elif status == "Terminal; Deliver As Is":
            return JiraStatus.TERMINAL_DELIVER_AS_IS
        elif status == "Partial Delivery; Will Rerun Remaining":
            return JiraStatus.PARTIAL_DELIVERY_WILL_RERUN_REMAINING
        elif status == "Deliver As Is; Will Not Rerun":
            return JiraStatus.DELIVER_AS_IS_WILL_NOT_RERUN
        elif status == "No Delivery; Will Reexecute":
            return JiraStatus.NO_DELIVERY_WILL_REEXECUTE
        elif status == "Primary Output Delivery":
            return JiraStatus.PRIMARY_OUTPUT_DELIVERY
        elif status == "Done":
            return JiraStatus.DONE
        elif status == "CI Review Needed":
            return JiraStatus.CI_REVIEW_NEEDED
        elif status == "Incomplete Request":
            return JiraStatus.INCOMPLETE_REQUEST
        elif status == "PM Hold":
            return JiraStatus.PM_HOLD
        elif status == "Missing Information":
            return JiraStatus.MISSING_INFORMATION
        else:
            return JiraStatus.UNKNOWN

    def post(self, request):
        issue = request.data['issue']['key']
        jira_status = request.data['issue']['fields']['status']['name']
        jbn = JobGroupNotifier.objects.filter(jira_id=issue).first()
        if jbn:
            jbn.status = self._convert_to_status(jira_status)
            jbn.save(update_fields=('status',))
            return Response(status=status.HTTP_200_OK)
        return Response(status.HTTP_400_BAD_REQUEST)


