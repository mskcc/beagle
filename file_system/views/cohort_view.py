from file_system.models import FileGroup
from file_system.serializers import CohortSerializer, CreateCohortSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, permissions
from rest_framework.permissions import IsAuthenticated


class CohortViewSet(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    GenericViewSet):
    queryset = FileGroup.objects.order_by('created_date').all()
    lookup_field = 'slug'
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return CohortSerializer
        return CreateCohortSerializer

