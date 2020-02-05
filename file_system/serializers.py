import os
from deepdiff import DeepDiff
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from file_system.metadata.validator import MetadataValidator
from file_system.models import File, Storage, StorageType, FileGroup, FileMetadata, FileType
from file_system.exceptions import MetadataValidationException


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
    file_group = FileGroupSerializer()
    metadata = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    def get_file_type(self, obj):
        return obj.file_type.name

    def get_metadata(self, obj):
        return Metadata(obj.filemetadata_set.first()).data.get('metadata', {})

    def get_user(self, obj):
        user_id = Metadata(obj.filemetadata_set.first()).data.get('user', None)
        if user_id:
            try:
                return User.objects.get(id=user_id).username
            except User.DoesNotExist:
                return None
        return None

    class Meta:
        model = File
        fields = ('id', 'file_name', 'file_type', 'path', 'size', 'file_group', 'metadata', 'user', 'created_date', 'modified_date')


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
        return file

    class Meta:
        model = File
        fields = ('path', 'file_type', 'size', 'file_group', 'metadata')


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

