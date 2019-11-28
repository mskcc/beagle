from rest_framework import serializers
from .models import Job


class JobSerializer(serializers.ModelSerializer):

    class Meta:
        model = Job
        fields = ('id', 'run', 'args', 'status', 'children', 'callback', 'callback_args', 'retry_count', 'message', 'max_retry')


class CreateJobSerializier(serializers.Serializer):
    type = serializers.CharField()
    args = serializers.JSONField()
    callback = serializers.CharField()
    callback_args = serializers.CharField()

    def create(self, validated_data):
        pass

    class Meta:
        model = Job
        fields = ('id', 'run', 'args', 'status', 'children', 'callback', 'callback_args', 'retry_count', 'message', 'max_retry')

