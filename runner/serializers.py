from rest_framework import serializers


class PipelineSerializer(serializers.Serializer):
    app = serializers.JSONField()
