import os
from file_system.models import File, Storage, StorageType, FileGroup, FileMetadata, Sample
from slugify import slugify
from rest_framework import serializers


class StorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Storage
        fields = ('id', 'name', 'type')


class CreateStorageSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=20)
    type = serializers.ChoiceField(choices=[(storage_type.value, storage_type.name) for storage_type in StorageType])

    # def create(self, data):
    #     storage = Storage.objects.create(name=data['name'], type=data['type'])
    #     return storage

    class Meta:
        model = Storage
        fields = ('name', 'type')


class CohortSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileGroup
        fields = ('id', 'name', 'slug', 'storage', 'metadata')


class CreateCohortSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileGroup
        fields = ('id', 'name', 'storage', 'metadata')


class Metadata(serializers.ModelSerializer):

    class Meta:
        model = FileMetadata
        fields = ('id', 'file', 'metadata', 'version', 'user')


class SampleSerializer(serializers.ModelSerializer):
    tags = serializers.JSONField(source='metadata')

    class Meta:
        model = Sample
        fields = ('id', 'sample_name', 'tags')


class FileSerializer(serializers.ModelSerializer):
    file_group = CohortSerializer(source='cohort')
    metadata = Metadata(many=True, source="filemetadata_set")
    sample = SampleSerializer()

    class Meta:
        model = File
        fields = ('id', 'file_name', 'path', 'size', 'file_group', 'sample', 'metadata', 'created_date', 'modified_date')


class CreateMetadata(serializers.ModelSerializer):

    class Meta:
        model = FileMetadata
        fields = ('file', 'metadata')


class CreateFileSerializer(serializers.ModelSerializer):
    path = serializers.CharField(max_length=400, required=True)
    size = serializers.IntegerField(required=True)
    cohort_id = serializers.UUIDField(required=True)
    sample_id = serializers.UUIDField(required=False, allow_null=True)
    metadata = CreateMetadata()

    class Meta:
        model = File
        fields = ('id', 'path', 'size', 'cohort_id', 'sample_id', 'metadata')






