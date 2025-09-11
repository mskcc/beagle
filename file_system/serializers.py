import os
from deepdiff import DeepDiff
from rest_framework import serializers
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from notifier.models import JobGroupNotifier
from beagle_etl.metadata.validator import MetadataValidator
from file_system.repository.file_repository import FileRepository
from file_system.models import File, Sample, Request, Patient, Storage, StorageType, FileGroup, FileMetadata, FileType
from file_system.exceptions import MetadataValidationException
from runner.models import Run, RunStatus
from drf_yasg import openapi


def ValidateDict(value):
    if len(value.split(":")) != 2:
        raise serializers.ValidationError("Query for inputs needs to be in format input:value")


def ValidateRegex(value):
    possible_queries = value.split("|")
    for single_query in possible_queries:
        if len(single_query.split(":")) != 2:
            raise serializers.ValidationError("Query for inputs needs to be in format input:value")


class PatchFile(serializers.JSONField):
    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_OBJECT,
            "title": "PatchFile",
            "properties": {
                "patch": openapi.Schema(
                    title="patch",
                    type=openapi.TYPE_OBJECT,
                ),
                "id": openapi.Schema(title="id", type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
            },
            "required": ["patch", "id"],
        }


class BatchPatchFileSerializer(serializers.Serializer):
    patch_files = serializers.ListField(child=PatchFile(required=True), allow_empty=False, required=True)


class StorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Storage
        fields = ("id", "name", "type")


class CreateStorageSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=20)
    type = serializers.ChoiceField(choices=[(storage_type.value, storage_type.name) for storage_type in StorageType])

    class Meta:
        model = Storage
        fields = ("name", "type")


class FileGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileGroup
        fields = ("id", "name", "slug", "storage", "owner")


class CreateFileGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileGroup
        fields = ("id", "name", "storage")


class Metadata(serializers.ModelSerializer):
    class Meta:
        model = FileMetadata
        fields = ("id", "metadata", "file", "version", "user")


class FileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileType
        fields = ("id", "name")


class CreateMetadata(serializers.ModelSerializer):
    metadata = serializers.JSONField()

    def validate_metadata(self, data):
        validator = MetadataValidator()
        try:
            validator.validate(data)
        except MetadataValidationException as e:
            raise serializers.ValidationError(e)

    class Meta:
        model = FileMetadata
        fields = ("file", "metadata")


class FileSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    file_group = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    checksum = serializers.SerializerMethodField()
    redacted = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.file.id

    def get_file_group(self, obj):
        return FileGroupSerializer(obj.file.file_group).data

    def get_file_type(self, obj):
        return obj.file.file_type.name

    def get_user(self, obj):
        if obj.user:
            try:
                return User.objects.get(id=obj.user.id).username
            except User.DoesNotExist:
                return None
        return None

    def get_file_name(self, obj):
        return obj.file.file_name

    def get_path(self, obj):
        return obj.file.path

    def get_size(self, obj):
        return obj.file.size

    def get_checksum(self, obj):
        return obj.file.checksum

    def get_redacted(self, obj):
        if obj.file.samples:
            sample = Sample.objects.filter(sample_id=obj.file.samples[0]).first()
            if sample:
                return sample.redact
        return "No sample associated with file"

    class Meta:
        model = FileMetadata
        fields = (
            "id",
            "file_name",
            "file_type",
            "path",
            "size",
            "file_group",
            "metadata",
            "user",
            "checksum",
            "redacted",
            "created_date",
            "modified_date",
        )


class FileQuerySerializer(serializers.Serializer):
    file_group = serializers.ListField(child=serializers.UUIDField(), allow_empty=True, required=False)
    path = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    exclude_null_metadata = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    order_by = serializers.CharField(required=False)
    distinct_metadata = serializers.CharField(required=False)
    metadata = serializers.ListField(
        child=serializers.CharField(validators=[ValidateDict]), allow_empty=True, required=False
    )
    metadata_regex = serializers.ListField(
        child=serializers.CharField(validators=[ValidateRegex]), allow_empty=True, required=False
    )
    path_regex = serializers.CharField(required=False)

    filename = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)

    filename_regex = serializers.CharField(required=False)

    file_type = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)

    values_metadata = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)

    created_date_timedelta = serializers.IntegerField(required=False)
    created_date_gt = serializers.DateTimeField(required=False)
    created_date_lt = serializers.DateTimeField(required=False)
    modified_date_timedelta = serializers.IntegerField(required=False)
    modified_date_gt = serializers.DateTimeField(required=False)
    modified_date_lt = serializers.DateTimeField(required=False)


class DistributionQuerySerializer(serializers.Serializer):
    file_group = serializers.ListField(child=serializers.UUIDField(), allow_empty=True, required=False)
    path = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    exclude_null_metadata = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    order_by = serializers.CharField(required=False)
    distinct_metadata = serializers.CharField(required=False)
    metadata = serializers.ListField(
        child=serializers.CharField(validators=[ValidateDict]), allow_empty=True, required=False
    )
    metadata_regex = serializers.ListField(
        child=serializers.CharField(validators=[ValidateRegex]), allow_empty=True, required=False
    )
    path_regex = serializers.CharField(required=False)

    filename = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)

    filename_regex = serializers.CharField(required=False)

    file_type = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)

    values_metadata = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)

    metadata_distribution = serializers.CharField(required=False)

    created_date_timedelta = serializers.IntegerField(required=False)
    created_date_gt = serializers.DateTimeField(required=False)
    created_date_lt = serializers.DateTimeField(required=False)
    modified_date_timedelta = serializers.IntegerField(required=False)
    modified_date_gt = serializers.DateTimeField(required=False)
    modified_date_lt = serializers.DateTimeField(required=False)


class CreateFileSerializer(serializers.ModelSerializer):
    path = serializers.CharField(max_length=400, required=True)
    size = serializers.IntegerField(required=False)
    file_type = serializers.CharField(max_length=30, required=True)
    metadata = serializers.JSONField(allow_null=True)

    def validate(self, attrs):
        path = attrs.get("path")
        file_group = attrs.get("file_group")
        try:
            File.objects.get(path=path, file_group=file_group)
        except File.DoesNotExist:
            pass
        else:
            raise serializers.ValidationError(f"File with path: {path} already exists in file_group: {file_group}")
        return attrs

    def validate_file_type(self, file_type):
        try:
            file_type = FileType.objects.get(name=file_type)
        except FileType.DoesNotExist:
            raise serializers.ValidationError("Unknown file_type: %s" % file_type)
        return file_type

    def validate_metadata(self, data):
        validator = MetadataValidator()
        try:
            validator.validate(data)
        except MetadataValidationException as e:
            raise serializers.ValidationError(e)
        return data

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request and hasattr(request, "user") else None
        validated_data["file_name"] = os.path.basename(validated_data.get("path"))
        validated_data["file_type"] = validated_data["file_type"]
        metadata = validated_data.pop("metadata")
        validated_data["request_id"] = metadata.get(settings.REQUEST_ID_METADATA_KEY)
        validated_data["samples"] = [metadata.get(settings.SAMPLE_ID_METADATA_KEY)]
        validated_data["patient_id"] = metadata.get(settings.PATIENT_ID_METADATA_KEY)
        file = File.objects.create(**validated_data)
        FileMetadata.objects.create_or_update(file=file, metadata=metadata, user=user)
        return file

    class Meta:
        model = File
        fields = ("path", "file_type", "size", "file_group", "metadata", "checksum")

class CreateFileFormSerializer(CreateFileSerializer):
    class Meta:
        model = File
        fields = ("path", "file_type", "file_group", "metadata")


class UpdateFileSerializer(serializers.Serializer):
    path = serializers.CharField(
        max_length=400, required=False, validators=[UniqueValidator(queryset=File.objects.all())]
    )
    size = serializers.IntegerField(required=False)
    file_group_id = serializers.UUIDField(required=False)
    file_type = serializers.CharField(max_length=30, required=False)
    metadata = serializers.JSONField(required=False)
    user = serializers.IntegerField(required=False)

    def validate_metadata(self, data):
        validator = MetadataValidator()
        try:
            validator.validate(data)
        except MetadataValidationException as e:
            print("ERROR in validation")
            return data
        return data

    def validate_file_type(self, file_type):
        try:
            file_type = FileType.objects.get(name=file_type)
        except FileType.DoesNotExist:
            raise serializers.ValidationError("Unknown file_type: %s" % file_type)
        return file_type

    def _validate_which_metadata_fields_changed(self, metadata_diff, user):
        unchangeable_by_user = (
            settings.CMO_SAMPLE_CLASS_METADATA_KEY,
            settings.SAMPLE_CLASS_METADATA_KEY,
            settings.TUMOR_OR_NORMAL_METADATA_KEY,
            settings.BAITSET_METADATA_KEY,
            settings.RECIPE_METADATA_KEY,
            settings.PRESERVATION_METADATA_KEY,
        )
        if not user.username == settings.ETL_USER:
            updated_keys = [
                key.replace("root['", "").replace("']", "") for key in metadata_diff.get("values_changed", {}).keys()
            ]
            if any(key in updated_keys for key in unchangeable_by_user):
                raise serializers.ValidationError(
                    f"Fields {', '.join(unchangeable_by_user)} can only be updated by SMILE"
                )

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user if request and hasattr(request, "user") else None
        if not user:
            try:
                user = User.objects.get(id=validated_data.get("user"))
            except User.DoesNotExist:
                user = User.objects.get(username=settings.ETL_USER)
        instance.path = validated_data.get("path", instance.path)
        instance.file_name = os.path.basename(instance.path)
        instance.size = validated_data.get("size", instance.size)
        instance.file_group_id = validated_data.get("file_group_id", instance.file_group_id)
        instance.file_type = validated_data.get("file_type", instance.file_type)
        ddiff = DeepDiff(
            instance.filemetadata_set.order_by("-created_date").first().metadata,
            validated_data.get("metadata"),
            ignore_order=True,
        )
        self._validate_which_metadata_fields_changed(ddiff, user)
        FileMetadata.objects.create_or_update(
            file=instance.id, metadata=validated_data.get("metadata"), user=user, from_file=True
        )
        return instance


class SampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = (
            "id",
            "sample_id",
            "sample_name",
            "cmo_sample_name",
            "sample_type",
            "tumor_or_normal",
            "sample_class",
            "igo_qc_notes",
            "cas_qc_notes",
            "redact",
        )

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request and hasattr(request, "user") else None
        instance = Sample.objects.create_or_update_instance(
            validated_data.pop("sample_id"), **validated_data, user=user
        )
        return instance

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user if request and hasattr(request, "user") else None
        instance = Sample.objects.create_or_update_instance(sample_id=instance.sample_id, **validated_data, user=user)
        return instance


class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ("id", "request_id", "lab_head_name", "investigator_email", "investigator_name", "delivery_date")

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request and hasattr(request, "user") else None
        instance = Request.objects.create_or_update_instance(
            validated_data.pop("request_id"), **validated_data, user=user
        )
        return instance

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user if request and hasattr(request, "user") else None
        instance = Request.objects.create_or_update_instance(
            request_id=instance.request_id, **validated_data, user=user
        )
        return instance


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ("id", "patient_id", "sex")

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request and hasattr(request, "user") else None
        instance = Patient.objects.create_or_update_instance(validated_data["patient_id"], **validated_data, user=user)
        return instance

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user if request and hasattr(request, "user") else None
        instance = Patient.objects.create_or_update_instance(instance.patient_id, **validated_data, user=user)
        return instance


class SampleQuerySerializer(serializers.Serializer):
    project_id = serializers.CharField(required=True)


class RunSerializerPartial(serializers.ModelSerializer):
    request_id = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    jira_id = serializers.SerializerMethodField()
    investigator = serializers.SerializerMethodField()
    pi = serializers.SerializerMethodField()
    assay = serializers.SerializerMethodField()
    delivery_date = serializers.SerializerMethodField()

    def get_status(self, obj):
        return RunStatus(obj.status).name

    def get_request_id(self, obj):
        return obj.tags.get(settings.REQUEST_ID_METADATA_KEY)

    def get_jira_id(self, obj):
        jgn = (
            JobGroupNotifier.objects.filter(job_group=obj.job_group, jira_id__startswith=settings.JIRA_PREFIX)
            .order_by("-created_date")
            .first()
        )
        return jgn.jira_id if jgn else None

    def get_pi(self, obj):
        jgn = (
            JobGroupNotifier.objects.filter(job_group=obj.job_group, jira_id__startswith=settings.JIRA_PREFIX)
            .order_by("-created_date")
            .first()
        )
        return jgn.PI if jgn else None

    def get_investigator(self, obj):
        jgn = (
            JobGroupNotifier.objects.filter(job_group=obj.job_group, jira_id__startswith=settings.JIRA_PREFIX)
            .order_by("-created_date")
            .first()
        )
        return jgn.investigator if jgn else None

    def get_assay(self, obj):
        jgn = (
            JobGroupNotifier.objects.filter(job_group=obj.job_group, jira_id__startswith=settings.JIRA_PREFIX)
            .order_by("-created_date")
            .first()
        )
        return jgn.assay if jgn else None

    def get_delivery_date(self, obj):
        return Request.objects.filter(request_id=obj.tags.get(settings.REQUEST_ID_METADATA_KEY)).first().delivery_date

    class Meta:
        model = Run
        fields = (
            "id",
            "name",
            "message",
            "status",
            "request_id",
            "app",
            "created_date",
            "job_group",
            "jira_id",
            "investigator",
            "pi",
            "assay",
            "delivery_date",
        )


class FullSampleSerializer(serializers.ModelSerializer):
    runs = serializers.SerializerMethodField()
    tumor_or_normal = serializers.SerializerMethodField()
    patient_id = serializers.SerializerMethodField()

    def get_runs(self, obj):
        return RunSerializerPartial(obj.run_set.order_by("-created_date").all(), many=True).data

    def get_tumor_or_normal(self, obj):
        return FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: obj.sample_id}, values_metadata="tumorOrNormal"
        ).first()

    def get_patient_id(self, obj):
        return FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: obj.sample_id}, values_metadata=settings.PATIENT_ID_METADATA_KEY
        ).first()

    class Meta:
        model = Sample
        fields = (
            "id",
            "sample_id",
            "runs",
            "sample_name",
            "cmo_sample_name",
            "redact",
            "tumor_or_normal",
            "patient_id",
        )


class CopyFilesSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=50, required=False)
    primary_id = serializers.CharField(max_length=50, required=False)
    file_group_from = serializers.UUIDField(required=True)
    file_group_to = serializers.UUIDField(required=True)

    def validate(self, data):
        request_id = data.get("request_id")
        primary_id = data.get("primary_id")
        if not request_id and not primary_id:
            raise serializers.ValidationError("Either request_id or primary_id input is required.")
        return data


class ManifestSerializer(serializers.Serializer):
    request_id = serializers.ListField(child=serializers.CharField(), required=True)
