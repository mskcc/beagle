from file_system.models import Sample, SampleMetadata
from file_system.serializers import SampleSerializer, SampleSerializerFull
from rest_framework.viewsets import GenericViewSet
from django.db.models import Prefetch
from rest_framework import mixins, permissions


class SampleView(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       GenericViewSet):
    queryset = Sample.objects.order_by('created_date').prefetch_related(
                 Prefetch('samplemetadata_set',
                 queryset=SampleMetadata.objects.order_by('-version'))).all()

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            if self.request.query_params.get('full'):
                return SampleSerializerFull
            else:
                return SampleSerializer
        return SampleSerializer
