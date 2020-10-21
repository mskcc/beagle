from core.models import UserRegistrationRequest
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer,TokenRefreshSerializer
from rest_framework import serializers
from drf_yasg import openapi


class BeagleTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['user'] = {
            'email': user.email,
            'groups': user.mskuser.groups.split(',')
        }
        return token

    def validate(self,attrs):
        data = super().validate(attrs)
        email = self.user.email
        groups = self.user.mskuser.groups.split(',')
        data['user'] = {
            'email': email,
            'groups': groups
        }

        return data


class BeagleTokenRefreshSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)


class UserField(serializers.JSONField):

    class Meta:
        swagger_schema_fields = {
                "type": openapi.TYPE_OBJECT,
                "title": "user",
                "properties": {
                    "email": openapi.Schema(
                        title="email",
                        type=openapi.TYPE_STRING,
                        format=openapi.FORMAT_EMAIL
                    ),
                    "groups": openapi.Schema(
                        title="groups",
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                        )
                    )
                }

            }


class TokenResponsePairSerializer(serializers.Serializer):

    refresh = serializers.CharField()
    token = serializers.CharField()
    user = UserField()


class TokenResponseRefreshSerializer(serializers.Serializer):
    access = serializers.CharField()


class UserRegistrationRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserRegistrationRequest
        fields = ('username', 'first_name', 'last_name')
