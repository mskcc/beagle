from rest_framework import serializers
from .models import Job, JobStatus
from notifier.models import JobGroup
from beagle_etl.jobs.lims_etl_jobs import TYPES


class JobSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return JobStatus(obj.status).name

    class Meta:
        model = Job
        fields = (
            'id', 'run', 'args', 'status', 'children', 'callback', 'callback_args', 'retry_count', 'message',
            'max_retry', 'job_group')


class CreateJobSerializier(serializers.ModelSerializer):
    run = serializers.ChoiceField(choices=list(TYPES.keys()), required=True)
    args = serializers.JSONField()
    callback = serializers.ChoiceField(choices=list(TYPES.keys()), required=False, allow_null=True, allow_blank=True)
    callback_args = serializers.JSONField(required=False, allow_null=True)
    job_group = serializers.UUIDField()

    def create(self, validated_data):
        run = TYPES.get(validated_data['run'])
        callback = TYPES.get(validated_data.get('callback', None))
        try:
            jg = JobGroup.objects.get(id=validated_data.get('job_group'))
        except JobGroup.DoesNotExist:
            raise serializers.ValidationError("Unknown job_group: %s" % validated_data.get('job_group'))
        job = Job.objects.create(status=JobStatus.CREATED,
                                 run=run, args=validated_data.get('args'),
                                 callback=callback,
                                 callback_args=validated_data.get('callback_args', {}),
                                 job_group=jg)
        return job

    class Meta:
        model = Job
        fields = (
            'id', 'run', 'args', 'callback', 'callback_args', 'retry_count',
            'max_retry', 'job_group')


class RequestIdLimsPullSerializer(serializers.Serializer):
    request_ids = serializers.ListField(
        child=serializers.CharField(max_length=30)
    )

