from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer




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


class BeagleTokenObtainPairView(TokenObtainPairView):
    serializer_class = BeagleTokenObtainPairSerializer
