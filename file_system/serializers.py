import os
from deepdiff import DeepDiff
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from beagle_etl.models import Job, JobStatus
from beagle_etl.jobs import TYPES
from file_system.metadata.validator import MetadataValidator
from file_system.models import File, Storage, StorageType, FileGroup, FileMetadata, FileType
from file_system.exceptions import MetadataValidationException


def ValidateDict(value):
    if len(value.split(":")) !=2:
        raise serializers.ValidationError("Query for inputs needs to be in format input:value")

class StorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Storage
        fields = ('id', 'name', 'type')


class CreateStorageSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=20)
    type = serializers.ChoiceField(choices=[(storage_type.value, storage_type.name) for storage_type in StorageType])

    class Meta:
        model = Storage
        fields = ('name', 'type')


class FileGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileGroup
        fields = ('id', 'name', 'slug', 'storage')


class CreateFileGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileGroup
        fields = ('id', 'name', 'storage')


class Metadata(serializers.ModelSerializer):

    class Meta:
        model = FileMetadata
        fields = ('id', 'metadata', 'file', 'version', 'user')


class FileTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileType
        fields = ('id', 'name')


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
        fields = ('file', 'metadata')


class FileSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    file_group = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    checksum = serializers.SerializerMethodField()

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

    class Meta:
        model = FileMetadata
        fields = ('id', 'file_name', 'file_type', 'path', 'size', 'file_group', 'metadata', 'user', 'checksum', 'created_date', 'modified_date')

class FileQuerySerializer(serializers.Serializer):
    file_group = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=True,
        required=False
    )
    path = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False
    )
    metadata = serializers.ListField(
        child=serializers.CharField(validators=[ValidateDict]),
        allow_empty=True,
        required=False
    )
    metadata_regex = serializers.ListField(
        child=serializers.CharField(validators=[ValidateDict]),
        allow_empty=True,
        required=False
    )
    path_regex = serializers.CharField(required=False)

    filename = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False
    )

    filename_regex = serializers.CharField(required=False)

    file_type = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False
    )

    values_metadata = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False
    )

    metadata_distribution = serializers.CharField(required=False)

    count = serializers.BooleanField(required=False)

    created_date_timedelta = serializers.IntegerField(required=False)
    created_date_gt = serializers.DateTimeField(required=False)
    created_date_lt = serializers.DateTimeField(required=False)
    modified_date_timedelta = serializers.IntegerField(required=False)
    modified_date_gt = serializers.DateTimeField(required=False)
    modified_date_lt = serializers.DateTimeField(required=False)


class CreateFileSerializer(serializers.ModelSerializer):
    path = serializers.CharField(max_length=400, required=True,
                                 validators=[UniqueValidator(queryset=File.objects.all())])
    size = serializers.IntegerField(required=False)
    # file_group_id = serializers.UUIDField(required=True)
    file_type = serializers.CharField(max_length=30, required=True)
    metadata = serializers.JSONField(allow_null=True)

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
        validated_data['file_name'] = os.path.basename(validated_data.get('path'))
        validated_data['file_type'] = validated_data['file_type']
        metadata = validated_data.pop('metadata')
        file = File.objects.create(**validated_data)
        metadata = FileMetadata(file=file, metadata=metadata, user=user)
        metadata.save()
        job = Job.objects.create(run=TYPES["CALCULATE_CHECKSUM"],
                                 args={'file_id': str(file.id), 'path': validated_data.get('path')},
                                 status=JobStatus.CREATED, max_retry=3, children=[])
        return file

    class Meta:
        model = File
        fields = ('path', 'file_type', 'size', 'file_group', 'metadata', 'checksum')


class UpdateFileSerializer(serializers.Serializer):
    path = serializers.CharField(max_length=400, required=False,
                                 validators=[UniqueValidator(queryset=File.objects.all())])
    size = serializers.IntegerField(required=False)
    file_group_id = serializers.UUIDField(required=False)
    file_type = serializers.CharField(max_length=30, required=False)
    metadata = serializers.JSONField(required=False)

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

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user if request and hasattr(request, "user") else None
        instance.path = validated_data.get('path', instance.path)
        instance.file_name = os.path.basename(instance.path)
        instance.size = validated_data.get('size', instance.size)
        instance.file_group_id = validated_data.get('file_group_id', instance.file_group_id)
        instance.file_type = validated_data.get('file_type', instance.file_type)
        ddiff = DeepDiff(validated_data.get('metadata'), instance.filemetadata_set.first().metadata, ignore_order=True)
        if ddiff:
            metadata = FileMetadata(file=instance, metadata=validated_data.get('metadata'), user=user)
            metadata.save()
        instance.save()
        return instance


# class BatchCreateFileSerializer(serializers.Serializer):
#     files = serializers.ListField(required=True, allow_empty=False)
#     metadata = serializers.JSONField(allow_null=True, default=dict)
#     file_group = serializers.UUIDField(required=True)
#
#     def create(self, validated_data):
#         request = self.context.get("request")
#         user = request.user if request and hasattr(request, "user") else None
#         sample = Sample(name=validated_data['name'])
#         sample.save()
#         metadata = SampleMetadata(sample=sample, metadata=validated_data['metadata'], user=user)
#         metadata.save()
#         file_group = FileGroup.objects.get(id=validated_data['file_group'])
#         for file in validated_data['files']:
#             File(file_name=os.path.basename(file), path=file, file_group=file_group, sample=sample).save()
#         return sample

