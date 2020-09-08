from rest_framework import serializers
from .models import Job, JobStatus, ETLConfiguration
from notifier.models import JobGroup
from beagle_etl.jobs import TYPES


def ValidateDict(value):
    if len(value.split(":")) !=2:
        raise serializers.ValidationError("Query for inputs needs to be in format input:value")

class JobSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return JobStatus(obj.status).name

    class Meta:
        model = Job
        fields = (
            'id', 'run', 'args', 'status', 'children', 'callback', 'callback_args', 'retry_count', 'message',
            'max_retry', 'job_group', 'finished_date', 'created_date', 'modified_date')


class AssaySerializer(serializers.ModelSerializer):

    class Meta:
        model = ETLConfiguration
        fields = '__all__'


class JobsTypesSerializer(serializers.Serializer):
    job_types = serializers.JSONField(required=False)


class AssayElementSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    all = serializers.ListField(required=False,
                                child=serializers.CharField())
    disabled = serializers.ListField(required=False,
                                     child=serializers.CharField())
    hold = serializers.ListField(required=False,
                                 child=serializers.CharField())


class AssayUpdateSerializer(serializers.Serializer):
    all = serializers.ListField(required=False,
                                child=serializers.CharField())
    disabled = serializers.ListField(required=False,
                                     child=serializers.CharField())
    hold = serializers.ListField(required=False,
                                 child=serializers.CharField())


class JobQuerySerializer(serializers.Serializer):

    status = serializers.ChoiceField([(status.name, status.value) for status in JobStatus], allow_blank=True,
                                     required=False)

    job_group = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=True,
        required=False
    )

    type = serializers.ChoiceField([(k, v) for k, v in TYPES.items()], allow_blank=True,
                                   required=False)

    sample_id = serializers.CharField(required=False)

    request_id = serializers.CharField(required=False)

    count = serializers.BooleanField(required=False)

    values_args = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False
    )

    args_distribution = serializers.CharField(required=False)

    args = serializers.ListField(
        child=serializers.CharField(validators=[ValidateDict]),
        allow_empty=True,
        required=False
    )

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
    retry = serializers.BooleanField(default=False)
