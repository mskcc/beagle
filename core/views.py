from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer, TokenVerifySerializer
from .serializers import BeagleTokenObtainPairSerializer, TokenResponsePairSerializer, TokenResponseRefreshSerializer
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers


class BeagleTokenObtainPairView(TokenObtainPairView):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair as well as the user's email address and groups.
    """
    serializer_class = BeagleTokenObtainPairSerializer

    @swagger_auto_schema(request_body=BeagleTokenObtainPairSerializer, responses={201: TokenResponsePairSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class BeagleTokenRefreshView(TokenRefreshView):
    """
    Takes a refresh type JSON web token and returns an access type JSON web
    token if the refresh token is valid.
    """
    serializer_class = TokenRefreshSerializer

    @swagger_auto_schema(request_body=TokenRefreshSerializer, responses={201: TokenResponseRefreshSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class BeagleTokenVerifyView(TokenVerifyView):
    """
    Takes a token and indicates if it is valid.  This view provides no
    information about a token's fitness for a particular use.
    """
    serializer_class = TokenVerifySerializer

    @swagger_auto_schema(request_body=TokenVerifySerializer, responses={201: serializers.Serializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
