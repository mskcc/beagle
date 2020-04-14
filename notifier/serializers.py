from .models import JobGroup
from rest_framework import serializers


class JobGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobGroup
        fields = ('id', 'created_date', 'jira_id')


class NotificationSerializer(serializers.Serializer):
    job_group = serializers.UUIDField(required=True)
    notification = serializers.CharField()
    arguments = serializers.JSONField()
