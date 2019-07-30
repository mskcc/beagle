import os
from file_system.models import File, Storage, StorageType, FileGroup, SampleMetadata, Sample
from rest_framework import serializers


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
        fields = ('id', 'name', 'slug', 'storage', 'metadata')


class CreateFileGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileGroup
        fields = ('id', 'name', 'storage', 'metadata')


class Metadata(serializers.ModelSerializer):

    class Meta:
        model = SampleMetadata
        fields = ('id', 'metadata', 'sample', 'version', 'user')


class CreateMetadata(serializers.ModelSerializer):

    class Meta:
        model = SampleMetadata
        fields = ('sample', 'metadata')


class SampleSerializer(serializers.ModelSerializer):
    metadata = serializers.SerializerMethodField()

    def get_metadata(self, obj):
        return Metadata(obj.samplemetadata_set.first()).data

    class Meta:
        model = Sample
        fields = ('id', 'name', 'tags', 'metadata')


class SampleSerializerFull(serializers.ModelSerializer):
    metadata = Metadata(source='samplemetadata_set', many=True)

    class Meta:
        model = Sample
        fields = ('id', 'name', 'tags', 'metadata')


class FileSerializer(serializers.ModelSerializer):
    file_group = FileGroupSerializer()
    sample = SampleSerializer()

    class Meta:
        model = File
        fields = ('id', 'file_name', 'path', 'size', 'file_group', 'lane', 'pair_end', 'sample', 'created_date', 'modified_date')


class CreateFileSerializer(serializers.Serializer):
    path = serializers.CharField(max_length=400, required=True)
    size = serializers.IntegerField(required=True)
    file_group_id = serializers.UUIDField(required=True)
    sample_id = serializers.UUIDField(required=True, allow_null=True)
    lane = serializers.IntegerField(required=False)
    pair_end = serializers.IntegerField(required=False)

    def create(self, validated_data):
        validated_data['file_name'] = os.path.basename(validated_data.get('path'))
        return File.objects.create(**validated_data)

    class Meta:
        model = File
        fields = ('id', 'path', 'size', 'cohort_id', 'sample_id', 'metadata')






