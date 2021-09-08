from .models import JobGroup
from rest_framework import serializers


class JobGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobGroup
        fields = ('id', 'created_date', 'jira_id')


class NotificationSerializer(serializers.Serializer):
    job_notifier = serializers.UUIDField(required=True)
    notification = serializers.CharField()
    arguments = serializers.JSONField()


class CreateNotifierSerializer(serializers.Serializer):
    job_group = serializers.UUIDField()
    pipeline = serializers.CharField(max_length=100)
    request_id = serializers.CharField(max_length=50)


class JobGroupQuerySerializer(serializers.Serializer):
    jira_id = serializers.CharField(allow_blank=False)


class JiraStatusSerializer(serializers.Serializer):
    timestamp = serializers.IntegerField()
    webhookEvent = serializers.CharField()
    issue_event_type_name = serializers.CharField()
    user = serializers.JSONField()
    issue = serializers.JSONField(required=True)
    changelog = serializers.JSONField()
