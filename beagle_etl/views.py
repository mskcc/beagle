from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from beagle_etl.models import ETLConfiguration
from drf_yasg.utils import swagger_auto_schema
from .serializers import (
    AssaySerializer,
    AssayElementSerializer,
    AssayUpdateSerializer,
)


class AssayViewSet(GenericAPIView):
    serializer_class = AssaySerializer
    queryset = ETLConfiguration.objects.all()
    pagination_class = None

    @swagger_auto_schema(responses={200: AssayElementSerializer})
    def get(self, request):
        assay = ETLConfiguration.objects.first()
        if assay:
            assay_response = AssaySerializer(assay)
            return Response(assay_response.data, status=status.HTTP_200_OK)
        error_message_list = ["Assay list is empty"]
        return Response({"errors": error_message_list}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(request_body=AssayUpdateSerializer, responses={200: AssayElementSerializer})
    def post(self, request):
        request_data = dict(request.data)
        all_list = request_data.get("all")
        disabled_list = request_data.get("disabled")
        hold_list = request_data.get("hold")
        assay = ETLConfiguration.objects.first()
        error_message_list = []
        if assay:
            if all_list:
                assay.all_recipes = list(set(all_list))
            if disabled_list:
                assay.disabled_recipes = list(set(disabled_list))
            if hold_list:
                assay.hold_recipes = list(set(hold_list))
            for single_assay in assay.hold_recipes:
                if single_assay in assay.disabled_recipes:
                    error_message = "Assay {} is in both disabled and hold".format(single_assay)
                    error_message_list.append(error_message)
            combined_list = assay.hold_recipes + assay.disabled_recipes
            for single_assay in combined_list:
                if single_assay not in assay.all_recipes:
                    error_message = "Assay {} is not listed in all".format(single_assay)
                    error_message_list.append(error_message)
            if error_message_list:
                return Response({"errors": list(set(error_message_list))}, status=status.HTTP_400_BAD_REQUEST)
            assay.save()
            assay_response = AssaySerializer(assay)
            return Response(assay_response.data, status=status.HTTP_200_OK)
        error_message_list = ["Assay list is empty"]
        return Response({"errors": error_message_list}, status=status.HTTP_404_NOT_FOUND)
