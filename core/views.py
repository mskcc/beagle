from rest_framework import mixins
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer, TokenVerifySerializer
from rest_framework.exceptions import AuthenticationFailed
from .models import UserRegistrationRequest
from .serializers import BeagleTokenObtainPairSerializer, TokenResponsePairSerializer, TokenResponseRefreshSerializer, \
    UserRegistrationRequestSerializer
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import AllowAny


class BeagleTokenObtainPairView(TokenObtainPairView):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair as well as the user's email address and groups.
    """
    serializer_class = BeagleTokenObtainPairSerializer

    @swagger_auto_schema(request_body=BeagleTokenObtainPairSerializer, responses={201: TokenResponsePairSerializer})
    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except AuthenticationFailed as auth_failed:
            error_message = {'detail': 'Invalid username or password'}
            return Response(error_message, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as auth_exception:
            print(auth_exception)
            error_message = {'detail': 'Unable to connect to authentication server'}
            return Response(error_message, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class BeagleTokenRefreshView(TokenRefreshView):
    """
    Takes a refresh type JSON web token and returns an access type JSON web
    token if the refresh token is valid.
    """
    serializer_class = TokenRefreshSerializer

    @swagger_auto_schema(request_body=TokenRefreshSerializer, responses={201: TokenResponseRefreshSerializer})
    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as auth_exception:
            error_message = {'detail': 'Unable to connect to authentication server'}
            return Response(error_message, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class BeagleTokenVerifyView(TokenVerifyView):
    """
    Takes a token and indicates if it is valid.  This view provides no
    information about a token's fitness for a particular use.
    """
    serializer_class = TokenVerifySerializer

    @swagger_auto_schema(request_body=TokenVerifySerializer, responses={201: serializers.Serializer})
    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as auth_exception:
            error_message = {'detail': 'Unable to connect to authentication server'}
            return Response(error_message, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class UserRequestViewSet(mixins.CreateModelMixin, GenericViewSet):
    serializer_class = UserRegistrationRequestSerializer
    queryset = UserRegistrationRequest.objects.order_by('created_date').all()
    permission_classes = (AllowAny,)
