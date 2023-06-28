from django.conf import settings
from django.db import transaction, IntegrityError
from rest_framework import mixins
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from file_system.serializers import (
    ManifestSerializer,
)
from drf_yasg.utils import swagger_auto_schema
from beagle.pagination import time_filter
from beagle.common import fix_query_list
from rest_framework.generics import GenericAPIView
from file_system.helper.access_helper import CmoDMPManifest


class Manifest(GenericAPIView):
    """GenericAPIView Class that returns a special formated csv, which adds DMP BAM Metadata to Request Fastq Metdata"""

    # Setting members
    pagination_class = None  # We don't need pagination
    serializer_class = ManifestSerializer

    @swagger_auto_schema(query_serializer=ManifestSerializer)
    def get(self, request):
        """get params, validate, return"""
        serializer = ManifestSerializer(data=request.query_params)
        if serializer.is_valid():
            request_ids = serializer.validated_data.get("request_id")
            try:
                # generate csv response
                response = CmoDMPManifest(request_ids).csv
            except ValidationError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
            if response is not None:
                return response
            else:
                return Response([], status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
