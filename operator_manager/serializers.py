from rest_framework import serializers
from notifier.models import Notifier
from operator_manager.models import Operator, OperatorStatus, OperatorVersion


class EnumNameField(serializers.ChoiceField):
    """Expose an IntEnum-backed IntegerField by member name (e.g. "READY") instead of its integer value."""

    def __init__(self, enum, **kwargs):
        self.enum = enum
        super().__init__(choices=[member.name for member in enum], **kwargs)

    def to_representation(self, value):
        # drf-yasg renders the choices (member names) through this method too
        if isinstance(value, str) and value in self.enum.__members__:
            return value
        return self.enum(value).name

    def to_internal_value(self, data):
        try:
            return self.enum[data].value
        except (KeyError, TypeError):
            self.fail("invalid_choice", input=data)


class OperatorSerializer(serializers.ModelSerializer):
    type = EnumNameField(OperatorVersion)
    status = EnumNameField(OperatorStatus, read_only=True)
    notifier = serializers.PrimaryKeyRelatedField(queryset=Notifier.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Operator
        fields = (
            "id",
            "name",
            "type",
            "class_name",
            "github_url",
            "version",
            "docker_image_tag",
            "docker_image_id",
            "status",
            "trigger",
            "notifier",
            "active",
        )
        # Populated by the image build (see Operator.ready)
        read_only_fields = ("docker_image_tag", "docker_image_id")

    def validate_trigger(self, value):
        if value is not None and not (isinstance(value, list) and all(isinstance(r, str) for r in value)):
            raise serializers.ValidationError("trigger must be a list of strings")
        return value


class OperatorQuerySerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    type = serializers.ChoiceField([member.name for member in OperatorVersion], required=False)
    status = serializers.ChoiceField([member.name for member in OperatorStatus], required=False)
    active = serializers.BooleanField(required=False, allow_null=True, default=None)
    trigger = serializers.CharField(required=False)
