from django.conf import settings
from rest_framework import status
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from runner.models import OperatorSDK
from runner.serializers import OperatorSDKSerializer, CreateOperatorSDKSerializer


class SDKOperatorViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericViewSet
):
    queryset = OperatorSDK.objects.all()

    def create(self, request, *args, **kwargs):
        sdk_operator = CreateOperatorSDKSerializer(data=request.data, context={"request": request})
        if sdk_operator.is_valid():
            operator = sdk_operator.save()
            response = OperatorSDKSerializer(operator)
            return Response(response.data, status=status.HTTP_201_CREATED)
        return Response(sdk_operator.errors, status=status.HTTP_400_BAD_REQUEST)