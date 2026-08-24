from rest_framework import serializers
from .models import ETLConfiguration, SMILEMessage, SmileMessageStatus


def ValidateDict(value):
    if len(value.split(":")) != 2:
        raise serializers.ValidationError("Query for inputs needs to be in format input:value")


class AssaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ETLConfiguration
        fields = "__all__"


class AssayElementSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    all = serializers.ListField(required=False, child=serializers.CharField())
    disabled = serializers.ListField(required=False, child=serializers.CharField())
    hold = serializers.ListField(required=False, child=serializers.CharField())


class AssayUpdateSerializer(serializers.Serializer):
    all = serializers.ListField(required=False, child=serializers.CharField())
    disabled = serializers.ListField(required=False, child=serializers.CharField())
    hold = serializers.ListField(required=False, child=serializers.CharField())


class RequestIdLimsPullSerializer(serializers.Serializer):
    request_ids = serializers.ListField(child=serializers.CharField(max_length=30))
    redelivery = serializers.BooleanField(default=False)


class SMILEMessageSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = SMILEMessage
        fields = "__all__"

    def get_status(self, obj):
        return SmileMessageStatus(obj.status).name


class SMILEMessageListSerializer(serializers.Serializer):
    request_id = serializers.CharField(required=False)
    topic = serializers.CharField(required=False)
    gene_panel = serializers.CharField(required=False)
    status = serializers.ChoiceField([(s.name, s.value) for s in SmileMessageStatus], allow_blank=True, required=False)
