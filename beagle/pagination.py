import math
import logging
from datetime import datetime, timedelta
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator
from django.utils.functional import cached_property


logger = logging.getLogger()


class BeaglePagination(PageNumberPagination):
    page_size_query_param = "page_size"

    def django_paginator_class(self, queryset, page_size):
        return CountFastPaginator(queryset, page_size)

    def get_paginated_response(self, data):
        return Response(
            {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "count": self.page.paginator.count,
                "last": math.ceil(self.page.paginator.count / len(data)) if len(data) != 0 else 1,
                "results": data,
            }
        )

    def get_page_size(self, request):
        if self.page_size_query_param:
            page_size = int(request.query_params.get(self.page_size_query_param, self.page_size))
            if page_size > 0:
                return page_size
            if page_size == 0:
                return None
        return self.page_size


class CountFastPaginator(Paginator):
    @cached_property
    def count(self):
        return self.object_list.values("id").count()


def time_filter(model, query_params, time_fields=("created_date", "modified_date"), previous_queryset=None):
    queryset = previous_queryset if previous_queryset is not None else model.objects.all()

    for time_field in time_fields:
        timedelta_param = f"{time_field}_timedelta"
        gt_param = f"{time_field}_gt"
        lt_param = f"{time_field}_lt"

        if timedelta_param in dict(query_params).keys():
            try:
                hours = int(query_params[timedelta_param])
                time_threshold = datetime.now() - timedelta(hours=hours)
                queryset = queryset.filter(**{f"{time_field}__gt": time_threshold})
            except (ValueError, TypeError) as e:
                logger.error(f"Error in time filter {e}")

        if gt_param in query_params:
            gt_value = query_params[gt_param]
            try:
                queryset = queryset.filter(**{f"{time_field}__gt": gt_value})
            except (ValueError, TypeError) as e:
                logger.error(f"Error in time filter {e}")

        if lt_param in query_params:
            lt_value = query_params[lt_param]
            try:
                queryset = queryset.filter(**{f"{time_field}__lt": lt_value})
            except (ValueError, TypeError) as e:
                logger.error(f"Error in time filter {e}")

    return queryset
