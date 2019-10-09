from rest_framework import serializers
from .models import Job


class JobSerializer(serializers.ModelSerializer):

    class Meta:
        model = Job
        fields = ('id', 'run', 'args', 'status', 'children', 'retry_count', 'message', 'max_retry')


class CreateJobSerialzier(serializers.Serializer):
    type = serializers.CharField()
    args = serializers.JSONField()
