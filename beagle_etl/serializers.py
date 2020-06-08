from rest_framework import serializers
from .models import Job, JobStatus, Assay
from notifier.models import JobGroup
from beagle_etl.jobs import TYPES


class JobSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return JobStatus(obj.status).name

    class Meta:
        model = Job
        fields = (
            'id', 'run', 'args', 'status', 'children', 'callback', 'callback_args', 'retry_count', 'message',
            'max_retry', 'job_group')


class AssaySerializer(serializers.ModelSerializer):

    class Meta:
        model = Assay
        fields = '__all__'

class JobQuerySerializer(serializers.Serializer):

    status = serializers.ChoiceField([(status.name, status.value) for status in JobStatus], allow_blank=True,
                                     required=False)

    job_group = serializers.ListField(required=False)

    type = serializers.ChoiceField([(k, v) for k, v in TYPES.items()], allow_blank=True,
                                   required=False)

    sample_id = serializers.CharField(required=False)

    request_id = serializers.CharField(required=False)

    created_date_timedelta = serializers.IntegerField(required=False)
    created_date_gt = serializers.DateTimeField(required=False)
    created_date_lt = serializers.DateTimeField(required=False)
    modified_date_timedelta = serializers.IntegerField(required=False)
    modified_date_gt = serializers.DateTimeField(required=False)
    modified_date_lt = serializers.DateTimeField(required=False)


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

