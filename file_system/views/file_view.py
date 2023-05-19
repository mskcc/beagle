from django.conf import settings
from django.db import transaction, IntegrityError
from rest_framework import mixins
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from file_system.repository import FileRepository
from file_system.models import File, FileMetadata
from file_system.exceptions import FileNotFoundException
from django.core.exceptions import ValidationError
from file_system.serializers import (
    CreateFileSerializer,
    UpdateFileSerializer,
    FileSerializer,
    FileQuerySerializer,
    BatchPatchFileSerializer,
    CopyFilesSerializer,
    manifestSerializer,
)
from drf_yasg.utils import swagger_auto_schema
from beagle.pagination import time_filter
from beagle.common import fix_query_list
from rest_framework.generics import GenericAPIView
import csv
from django.http import HttpResponse


class FileView(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):

    queryset = FileMetadata.objects.order_by("file", "-version").distinct("file")
    permission_classes = (IsAuthenticated,)
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_serializer_class(self):
        return FileSerializer

    def destroy(self, request, *args, **kwargs):
        try:
            FileRepository.delete(kwargs["pk"])
        except FileNotFoundException as e:
            return Response({"details": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        try:
            f = FileRepository.get(kwargs["pk"])
        except FileNotFoundException as e:
            return Response({"details": str(e)}, status=status.HTTP_404_NOT_FOUND)
        serializer = FileSerializer(f)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(query_serializer=FileQuerySerializer)
    def list(self, request, *args, **kwargs):
        query_list_types = [
            "file_group",
            "path",
            "metadata",
            "metadata_regex",
            "filename",
            "file_type",
            "values_metadata",
            "exclude_null_metadata",
        ]
        fixed_query_params = fix_query_list(request.query_params, query_list_types)
        serializer = FileQuerySerializer(data=fixed_query_params)
        if serializer.is_valid():
            queryset = FileRepository.all()
            queryset = time_filter(
                FileMetadata, request.query_params, time_modal="modified_date", previous_queryset=queryset
            )
            file_group = fixed_query_params.get("file_group")
            path = fixed_query_params.get("path")
            metadata = fixed_query_params.get("metadata")
            metadata_regex = fixed_query_params.get("metadata_regex")
            path_regex = fixed_query_params.get("path_regex")
            filename = fixed_query_params.get("filename")
            filename_regex = fixed_query_params.get("filename_regex")
            file_type = fixed_query_params.get("file_type")
            values_metadata = fixed_query_params.get("values_metadata")
            exclude_null_metadata = fixed_query_params.get("exclude_null_metadata")
            order_by = fixed_query_params.get("order_by")
            distinct_metadata = fixed_query_params.get("distinct_metadata")
            kwargs = {"queryset": queryset}
            if file_group:
                if len(file_group) == 1:
                    kwargs["file_group"] = file_group[0]
                else:
                    kwargs["file_group_in"] = file_group
            if path:
                if len(path) == 1:
                    kwargs["path"] = path[0]
                else:
                    kwargs["path_in"] = path
            if metadata:
                filter_query = dict()
                for val in metadata:
                    k, v = val.split(":")
                    metadata_field = k.strip()
                    if metadata_field not in filter_query:
                        filter_query[metadata_field] = [v.strip()]
                    else:
                        filter_query[metadata_field].append(v.strip())
                if filter_query:
                    kwargs["metadata"] = filter_query
            if metadata_regex:
                filter_query = []
                for single_reqex_query in metadata_regex:
                    single_value = single_reqex_query.split("|")
                    single_reqex_filters = []
                    for val in single_value:
                        k, v = val.split(":")
                        single_reqex_filters.append((k.strip(), v.strip()))
                    filter_query.append(single_reqex_filters)
                if filter_query:
                    kwargs["metadata_regex"] = filter_query
            if path_regex:
                kwargs["path_regex"] = path_regex
            if filename:
                if len(filename) == 1:
                    kwargs["file_name"] = filename[0]
                else:
                    kwargs["file_name_in"] = filename
            if filename_regex:
                kwargs["file_name_regex"] = filename_regex
            if file_type:
                if len(file_type) == 1:
                    kwargs["file_type"] = file_type[0]
                else:
                    kwargs["file_type_in"] = file_type
            if exclude_null_metadata:
                kwargs["exclude"] = exclude_null_metadata
            if order_by:
                kwargs["order_by"] = order_by
            if distinct_metadata:
                kwargs["distinct"] = distinct_metadata
            if values_metadata:
                if len(values_metadata) == 1:
                    kwargs["key_values_metadata"] = values_metadata[0]
                else:
                    kwargs["key_values_metadata_list"] = values_metadata
            try:
                queryset = FileRepository.filter(**kwargs)
            except Exception as e:
                return Response({"details": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            page = self.paginate_queryset(queryset)
            if page is not None:
                if values_metadata:
                    return self.get_paginated_response(page)
                else:
                    serializer = FileSerializer(page, many=True, context={"request": request})
                    return self.get_paginated_response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        serializer = CreateFileSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            file = serializer.save()
            response = FileSerializer(file.filemetadata_set.first())
            return Response(response.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            f = FileRepository.get(id=kwargs.get("pk"))
        except FileNotFoundException:
            return Response({"details": "Not Found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UpdateFileSerializer(
            f.file, data=request.data, context={"request": request}, partial=request.method == "PATCH"
        )
        if serializer.is_valid():
            serializer.save()
            f = FileRepository.get(id=kwargs.get("pk"))
            response = FileSerializer(f)
            return Response(response.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, "_paginator"):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)


class BatchPatchFiles(GenericAPIView):

    queryset = FileMetadata.objects.order_by("file", "-version").distinct("file")
    serializer_class = BatchPatchFileSerializer

    def post(self, request):
        patch_files = request.data.get("patch_files", [])
        sid = transaction.savepoint()
        current_file_id = None
        current_file_data = None
        file_count = len(patch_files)
        try:
            for single_file_patch in patch_files:
                current_file_id = single_file_patch["id"]
                current_file_data = single_file_patch["patch"]
                f = FileRepository.get(id=current_file_id)
                serializer = UpdateFileSerializer(f.file, data=current_file_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.savepoint_rollback(sid)
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            transaction.savepoint_commit(sid)
        except FileNotFoundException:
            transaction.savepoint_rollback(sid)
            error_message = "File {} not found".format(current_file_id)
            return Response({"details": error_message}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            transaction.savepoint_rollback(sid)
            error_message = "Integrity error"
            return Response({"details": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            transaction.savepoint_rollback(sid)
            error_message = "An unexpected error occured: " + repr(e)
            return Response({"details": error_message}, status=status.HTTP_400_BAD_REQUEST)

        success_message = "Successfully updated {} files".format(file_count)
        return Response(success_message, status=status.HTTP_200_OK)


class CopyFilesView(GenericAPIView):
    def _copy_files(self, files, file_group):
        for f in files:
            new_file = f.file
            new_file.pk = None
            new_file.file_group_id = file_group
            new_file.save()
            f.pk = None
            f.file = new_file
            f.save()

    def post(self, request):
        serializer = CopyFilesSerializer(data=request.data)
        if serializer.is_valid():
            request_id = serializer.data.get("request_id")
            primary_id = serializer.data.get("primary_id")
            file_group_from = serializer.data["file_group_from"]
            file_group_to = serializer.data["file_group_to"]
            if primary_id:
                files = FileRepository.filter(
                    metadata={settings.SAMPLE_ID_METADATA_KEY: primary_id}, file_group=file_group_from
                )
            elif request_id:
                files = FileRepository.filter(
                    metadata={settings.REQUEST_ID_METADATA_KEY: request_id}, file_group=file_group_from
                )
            self._copy_files(files, file_group_to)
        return Response(status=status.HTTP_200_OK)


class manifest(GenericAPIView):
    """GenericAPIView Class that returns a special formated csv, which adds DMP BAM Metadata to Request Fastq Metdata"""

    # Setting members
    pagination_class = None  # We don't need pagination
    serializer_class = manifestSerializer
    # headers for returned csv
    manifestHeader = [
        "igoRequestId",
        "primaryId",
        "cmoPatientId",
        "cmoSampleIdFields",
        "dmpSampleInfo",
        "dmpPatientId",
        "baitSet",
        "libraryVolume",
        "investigatorSampleId",
        "preservation",
        "species",
        "libraryConcentrationNgul",
        "tissueLocation",
        "sampleClass",
        "sex",
        "cfDNA2dBarcode",
        "sampleOrigin",
        "tubeId",
        "tumorOrNormal",
        "captureConcentrationNm",
        "oncotreeCode",
        "dnaInputNg",
        "collectionYear",
        "captureInputNg",
    ]
    # varibales we want from the request metadata
    request_keys = [
        "igoRequestId",
        "primaryId",
        "cmoSampleIdFields",
        "cmoPatientId",
        "investigatorSampleId",
        "sampleClass",
        "oncotreeCode",
        "tumorOrNormal",
        "tissueLocation",
        "sampleOrigin",
        "preservation",
        "collectionYear",
        "sex",
        "species",
        "tubeId",
        "cfDNA2dBarcode",
        "baitSet",
        "libraryVolume",
        "libraryConcentrationNgul",
        "dnaInputNg",
        "captureConcentrationNm",
        "captureInputNg",
    ]

    def construct_csv(self, request_query, pDmps, request_ids):
        """
        Construct a csv HTTP response from DMP BAM Metadata and Request Metadata
        Keyword arguments:
            request_query -- a queryset containg fastq metaddata for a given request
            pDmps -- a query set from the DMP BAM file group, filtered to patients in request_query
        """
        # set up HTTP response
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="{request}.csv"'.format(request=request_ids)
        writer = csv.DictWriter(response, fieldnames=self.manifestHeader)
        writer.writeheader()
        # we care about the metadata for the request
        request_metadata = request_query.values_list("metadata", flat=True)
        primaryIds = set()  # we only want to look at fastq metdata for a PrimaryId once
        # for each fastq in the request query
        for fastq in request_metadata:
            pId = fastq["primaryId"]
            if pId not in primaryIds:  # we haven't seen the Primary Id
                primaryIds.add(pId)
                fastq_meta = {k: fastq[k] for k in fastq.keys() & self.request_keys}
                fastq_meta["dmpSampleInfo"] = None
                fastq_meta["dmpPatientId"] = None
                # look up cmopatient in dmp query set
                patient_id = fastq_meta["cmoPatientId"].replace("C-", "")
                dmp_meta = pDmps.filter(metadata__patient__cmo=patient_id)
                if dmp_meta.exists():
                    dmpsampleinfo = [dmp.metadata["sample"] for dmp in dmp_meta]
                    # add dmp data to request data, building up in csv
                    dmpsampleinfo = ";".join(dmpsampleinfo)
                    dmppatientid = dmp_meta[0].metadata["patient"]["dmp"]
                    fastq_meta["dmpSampleInfo"] = dmpsampleinfo
                    fastq_meta["dmpPatientId"] = dmppatientid
                writer.writerow(fastq_meta)
        return response

    @swagger_auto_schema(query_serializer=manifestSerializer)
    def get(self, request):
        """get params, validate, return"""
        serializer = manifestSerializer(data=request.query_params)
        if serializer.is_valid():
            request_ids = serializer.validated_data.get("request_id")
            if request_ids:
                # get fastq metadata for a given request
                request_query = FileMetadata.objects.filter(metadata__igoRequestId__in=request_ids)
                cmoPatientId = request_query.values_list("metadata__cmoPatientId", flat=True)
                cmoPatientId = list(set(list(cmoPatientId)))
                # get DMP BAM file group
                dmp_bams = FileRepository.filter(file_group=settings.DMP_BAM_FILE_GROUP)
                cmoPatientId_trim = [c.replace("C-", "") for c in cmoPatientId]
                # subset DMP BAM file group to patients in the provided requests
                pDmps = dmp_bams.filter(metadata__patient__cmo__in=cmoPatientId_trim)
            try:
                # generate csv response
                response = self.construct_csv(request_query, pDmps, request_ids)
            except ValidationError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
            if response is not None:
                return response
            else:
                return Response([], status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
