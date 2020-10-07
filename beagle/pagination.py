import math
from datetime import datetime, timedelta
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


class BeaglePagination(PageNumberPagination):
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'last': math.ceil(self.page.paginator.count / len(data)) if len(data) != 0 else 1,
            'results': data
        })

    def get_page_size(self, request):
        if self.page_size_query_param:
            page_size = int(request.query_params.get(self.page_size_query_param, self.page_size))
            if page_size > 0:
                return page_size
            elif page_size == 0:
                return None
            else:
                pass
        return self.page_size


def time_filter(model, query_params, time_modal='created_date', previous_queryset=None):
    timedelta_query = '%s_timedelta' % time_modal
    gt_query = '%s_gt' % time_modal
    gt_query_filter = '%s__gt' % time_modal
    lt_query = '%s_lt' % time_modal
    lt_query_filter = '%s__lt' % time_modal
    order_by = '-%s' % time_modal
    if query_params.get(timedelta_query):
        time_threshold = datetime.now() - timedelta(hours=int(query_params[timedelta_query]))
        queryset = model.objects.filter(**{gt_query_filter: time_threshold}).order_by(order_by)
    elif query_params.get(gt_query) or query_params.get(lt_query):
        if query_params.get(gt_query):
            time_gt = query_params[gt_query]
            queryset = model.objects.filter(**{gt_query_filter: time_gt}).order_by(order_by)
        if query_params.get(lt_query):
            time_lt = query_params[lt_query]
            queryset = model.objects.filter(**{lt_query_filter: time_lt}).order_by(order_by)

    else:
        if previous_queryset != None:
            queryset = previous_queryset
        else:
            queryset = model.objects.order_by(order_by).all()
    return queryset
