from rest_framework_simplejwt.serializers import TokenObtainPairSerializer,TokenRefreshSerializer
from rest_framework import serializers


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
