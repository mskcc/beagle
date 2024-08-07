import datetime
from django.conf import settings
from rest_framework import serializers
from notifier.models import JobGroup, JobGroupNotifier
from runner.exceptions import PortProcessorException
from runner.run.processors.port_processor import PortProcessor, PortAction
from runner.models import Pipeline, Run, Port, RunStatus, PortType, ExecutionEvents, OperatorErrors, OperatorRun


def ValidateDict(value):
    if len(value.split(":")) != 2:
        raise serializers.ValidationError("Query for inputs needs to be in format input:value")


def format_port_data(port_data):
    port_dict = {}
    for single_port in port_data:
        port_name = single_port["name"]
        try:
            port_value = PortProcessor.process_files(single_port["db_value"], PortAction.CONVERT_TO_CWL_FORMAT)
        except PortProcessorException as e:
            raise serializers.ValidationError(e)
        port_dict[port_name] = port_value
    return port_dict


class OperatorRunListSerializer(serializers.Serializer):
    app = serializers.UUIDField(required=False)
    app_name = serializers.CharField(required=False)
    app_version = serializers.CharField(required=False)
    tags = serializers.JSONField(required=False)
    status = serializers.ChoiceField(
        [(status.name, status.value) for status in RunStatus], allow_blank=True, required=False
    )


class RunApiListSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        [(status.name, status.value) for status in RunStatus], allow_blank=True, required=False
    )
    job_groups = serializers.ListField(child=serializers.UUIDField(), allow_empty=True, required=False)
    apps = serializers.ListField(child=serializers.UUIDField(), allow_empty=True, required=False)
    ports = serializers.ListField(
        child=serializers.CharField(validators=[ValidateDict]), allow_empty=True, required=False
    )
    tags = serializers.ListField(
        child=serializers.CharField(validators=[ValidateDict]), allow_empty=True, required=False
    )
    request_ids = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    sample_ids = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    jira_ids = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)

    run_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=True, required=False)

    values_run = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)

    run_distribution = serializers.CharField(required=False)

    run = serializers.ListField(
        child=serializers.CharField(validators=[ValidateDict]), allow_empty=True, required=False
    )

    full = serializers.BooleanField(required=False)
    count = serializers.BooleanField(required=False)

    created_date_timedelta = serializers.IntegerField(required=False)
    created_date_gt = serializers.DateTimeField(required=False)
    created_date_lt = serializers.DateTimeField(required=False)
    modified_date_timedelta = serializers.IntegerField(required=False)
    modified_date_gt = serializers.DateTimeField(required=False)
    modified_date_lt = serializers.DateTimeField(required=False)


class PipelineResolvedSerializer(serializers.Serializer):
    app = serializers.JSONField()


class PipelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pipeline
        fields = "__all__"


class PortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Port
        fields = "__all__"


class UpdatePortSerializer(serializers.Serializer):
    values = serializers.ListField()


class CreatePortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Port
        fields = ("run", "name", "port_type", "schema", "secondary_files", "value")


class CreateRunSerializer(serializers.Serializer):
    pipeline_id = serializers.UUIDField()
    request_id = serializers.CharField()

    def create(self, validated_data):
        try:
            pipeline = Pipeline.objects.get(pk=validated_data.get("pipeline_id"))
        except Pipeline.DoesNotExist:
            raise serializers.ValidationError("Unknown pipeline: %s" % validated_data.get("pipeline_id"))
        name = "Run %s: %s" % (pipeline.name, datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
        run = Run(
            run_type=pipeline.pipeline_type,
            name=name,
            app=pipeline,
            tags={settings.REQUEST_ID_METADATA_KEY: validated_data.get(settings.REQUEST_ID_METADATA_KEY)},
            status=RunStatus.CREATING,
            job_statuses=dict(),
            resume=validated_data.get("resume"),
        )
        run.save()
        return run


class UpdateRunSerializer(serializers.Serializer):
    status = serializers.IntegerField(required=False)
    job_statuses = serializers.JSONField(allow_null=True, required=False)

    def update(self, instance, validated_data):
        instance.status = validated_data.get("status", instance.status)
        instance.job_statuses = validated_data.get("status", instance.job_statuses)
        instance.save()
        return instance


class RunSerializerPartial(serializers.ModelSerializer):
    request_id = serializers.SerializerMethodField()
    status_url = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    samples = serializers.SerializerMethodField()

    def get_status(self, obj):
        return RunStatus(obj.status).name

    def get_request_id(self, obj):
        return obj.tags.get(settings.REQUEST_ID_METADATA_KEY)

    def get_status_url(self, obj):
        return settings.BEAGLE_URL + "/v0/run/api/%s" % obj.id

    def get_samples(self, obj):
        return obj.samples.all().values_list("sample_id", flat=True)

    class Meta:
        model = Run
        fields = (
            "id",
            "name",
            "message",
            "status",
            "samples",
            "request_id",
            "app",
            "status_url",
            "created_date",
            "job_group",
        )


class RunSerializerFull(serializers.ModelSerializer):
    inputs = serializers.SerializerMethodField()
    outputs = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    status_url = serializers.SerializerMethodField()

    def get_status(self, obj):
        return RunStatus(obj.status).name

    def get_inputs(self, obj):
        return PortSerializer(obj.port_set.filter(port_type=PortType.INPUT).all(), many=True).data

    def get_outputs(self, obj):
        return PortSerializer(obj.port_set.filter(port_type=PortType.OUTPUT).all(), many=True).data

    def get_status_url(self, obj):
        return settings.BEAGLE_URL + "/v0/run/api/%s" % obj.id

    class Meta:
        model = Run
        fields = (
            "id",
            "name",
            "status",
            "tags",
            "app",
            "inputs",
            "outputs",
            "status_url",
            "created_date",
            "started",
            "submitted",
            "job_statuses",
            "execution_id",
            "output_metadata",
            "output_directory",
            "operator_run",
            "job_group",
            "notify_for_outputs",
            "finished_date",
            "message",
        )


class RunSerializerCWLInput(RunSerializerPartial):

    inputs = serializers.SerializerMethodField()

    def get_inputs(self, obj):
        input_data = PortSerializer(obj.port_set.filter(port_type=PortType.INPUT).all(), many=True).data
        return format_port_data(input_data)

    class Meta:
        model = Run
        fields = ("id", "name", "inputs")


class RunSerializerCWLOutput(RunSerializerPartial):

    outputs = serializers.SerializerMethodField()

    def get_outputs(self, obj):
        output_data = PortSerializer(obj.port_set.filter(port_type=PortType.OUTPUT).all(), many=True).data
        return format_port_data(output_data)

    class Meta:
        model = Run
        fields = ("id", "name", "outputs")


class CWLJsonSerializer(serializers.Serializer):
    cwl_inputs = serializers.BooleanField(required=False)
    runs = serializers.ListField(child=serializers.UUIDField(), allow_empty=True, required=False)
    job_groups = serializers.ListField(child=serializers.UUIDField(), allow_empty=True, required=False)
    jira_ids = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    request_ids = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)


class RunStatusUpdateSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True)
    name = serializers.CharField(required=False)
    jobStatus = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    errFilePath = serializers.CharField(required=False)
    outputs = serializers.JSONField(required=False, allow_null=True)
    processed = serializers.BooleanField(required=False)

    def create(self, validated_data):
        event = ExecutionEvents()
        event.execution_id = validated_data.get("id", None)
        event.name = validated_data.get("name", None)
        event.job_status = validated_data.get("jobStatus", None)
        event.message = validated_data.get("message", None)
        event.err_file_path = validated_data.get("errFilePath", None)
        event.outputs = validated_data.get("outputs", None)
        event.processed = False
        event.save()

    def update(self, instance, validated_data):
        instance.processed = validated_data.get("processed")
        instance.save()


class RestartRunSerializer(serializers.Serializer):
    operator_run_id = serializers.UUIDField(required=True)
    clean = serializers.BooleanField(default=False)


# TODO: Delete this
class RequestIdOperatorSerializer(serializers.Serializer):
    request_ids = serializers.ListField(child=serializers.CharField(max_length=30), allow_empty=True)
    run_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=True)
    pipeline_name = serializers.CharField(max_length=100)


class RequestIdsOperatorSerializer(serializers.Serializer):
    request_ids = serializers.ListField(child=serializers.CharField(max_length=30), allow_empty=True)
    pipeline = serializers.CharField(max_length=30, allow_null=False, allow_blank=False)
    pipeline_version = serializers.CharField(max_length=30, allow_null=True, allow_blank=True)
    job_group_id = serializers.UUIDField(required=False)
    file_group_id = serializers.UUIDField(required=False)
    for_each = serializers.BooleanField(required=False, default=True)


class RunIdsOperatorSerializer(serializers.Serializer):
    run_ids = serializers.ListField(child=serializers.CharField(max_length=30), allow_empty=True)
    pipelines = serializers.ListField(child=serializers.CharField(max_length=30), allow_empty=True)
    pipeline_versions = serializers.ListField(child=serializers.CharField(max_length=30), allow_empty=True)
    job_group_id = serializers.UUIDField(required=False)
    for_each = serializers.BooleanField(default=False)


class PairOperatorSerializer(serializers.Serializer):
    pairs = serializers.ListField(child=serializers.JSONField(), allow_empty=True)
    pipelines = serializers.ListField(child=serializers.CharField(max_length=30), allow_empty=True)
    pipeline_versions = serializers.ListField(child=serializers.CharField(max_length=30), allow_empty=True)
    name = serializers.CharField(allow_blank=False, allow_null=False)
    output_directory_prefix = serializers.CharField(max_length=50, allow_blank=True, allow_null=True)
    job_group_id = serializers.UUIDField(required=False)
    file_group_id = serializers.UUIDField(required=False)
    request_id = serializers.CharField()
    labHeadName = serializers.CharField(max_length=30, required=False, allow_blank=True, allow_null=True)
    investigatorName = serializers.CharField(max_length=30, required=False, allow_blank=True, allow_null=True)
    assay = serializers.CharField(max_length=30, required=False, allow_blank=True, allow_null=True)


class OperatorErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperatorErrors
        fields = "__all__"


class OperatorRunSerializer(serializers.ModelSerializer):
    operator_class = serializers.SerializerMethodField()
    app_name = serializers.SerializerMethodField()
    app_version = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_app_name(self, obj):
        return obj.operator.pipeline_set.first().name

    def get_app_version(self, obj):
        return obj.operator.pipeline_set.first().version

    def get_operator_class(self, obj):
        return obj.operator.class_name

    def get_status(self, obj):
        return RunStatus(obj.status).name

    class Meta:
        model = OperatorRun
        fields = "__all__"


class AionOperatorSerializer(serializers.Serializer):
    lab_head_email = serializers.CharField(max_length=100)


class TempoMPGenOperatorSerializer(serializers.Serializer):
    normals_override = serializers.ListField(child=serializers.CharField(max_length=30), allow_empty=True)
    tumors_override = serializers.ListField(child=serializers.CharField(max_length=30), allow_empty=True)


class ArgosPairingSerializer(serializers.Serializer):
    argos_slug = serializers.CharField(default="ArgosOperator 2.0.0", allow_blank=False)
    igo_request_id = serializers.CharField(required=True, allow_blank=False)


class RunSamplesSerializer(serializers.Serializer):
    job_group = (serializers.ListField(child=serializers.UUIDField(), allow_empty=True, required=False),)
    samples = serializers.ListField(child=serializers.CharField(), allow_empty=False, required=True)


class OperatorLatestSamplesQuerySerializer(serializers.Serializer):
    samples = serializers.ListField(child=serializers.CharField(), allow_empty=False, required=True)


class OperatorSampleQuerySerializer(serializers.Serializer):
    sample = serializers.CharField(required=True, allow_blank=False)


class TerminateRunSerializer(serializers.Serializer):
    job_group_id = serializers.UUIDField(required=False, allow_null=True)
    runs = serializers.ListField(child=serializers.UUIDField())

    def validate(self, attrs):
        if attrs.get("job_group_id"):
            try:
                JobGroup.objects.get(id=attrs["job_group_id"])
            except JobGroup.DoesNotExist:
                raise serializers.ValidationError("JobGroup with id: %s doesn't exist." % attrs["job_group_id"])
        if attrs.get("runs", []):
            run_missing = []
            for run in attrs["runs"]:
                try:
                    Run.objects.get(id=run)
                except Run.DoesNotExist:
                    run_missing.append(str(run))
            if run_missing:
                raise serializers.ValidationError("Runs with id(s): %s doesn't exist." % ", ".join(run_missing))
        if not attrs.get("job_group_id") and not attrs.get("runs"):
            raise serializers.ValidationError("Either job_group_id or runs needs to be specified.")
        return attrs
