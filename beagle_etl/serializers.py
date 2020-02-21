from rest_framework import serializers
from .models import Job, JobStatus
from beagle_etl.jobs.lims_etl_jobs import TYPES


class JobSerializer(serializers.ModelSerializer):

    class Meta:
        model = Job
        fields = ('id', 'run', 'args', 'status', 'children', 'callback', 'callback_args', 'retry_count', 'message', 'max_retry')


class CreateJobSerializier(serializers.Serializer):
    run = serializers.ChoiceField(choices=list(TYPES.keys()), required=True)
    args = serializers.JSONField()
    callback = serializers.ChoiceField(choices=list(TYPES.keys()), required=False, allow_null=True, allow_blank=True)
    callback_args = serializers.JSONField(required=False, allow_null=True)

    def create(self, validated_data):
        run = TYPES.get(validated_data['run'])
        callback = TYPES.get(validated_data.get('callback', None))
        job = Job(status=JobStatus.CREATED, run=run, args=validated_data.get('args'), callback=callback,
                  callback_args=validated_data.get('callback_args', {}))
        job.save()
        return job

    class Meta:
        model = Job
        fields = ('id', 'run', 'args', 'status', 'children', 'callback', 'callback_args', 'retry_count', 'message', 'max_retry')


class RequestIdLimsPullSerializer(serializers.Serializer):
    request_ids = serializers.ListField(
        child=serializers.CharField(max_length=30)
    )

