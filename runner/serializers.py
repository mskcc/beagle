from rest_framework import serializers
from runner.models import Pipeline


class PipelineResolvedSerializer(serializers.Serializer):
    app = serializers.JSONField()


class PipelineSerializer(serializers.ModelSerializer):

    class Meta:
        model = Pipeline
        fields = ('id', 'name', 'github', 'version', 'entrypoint')
