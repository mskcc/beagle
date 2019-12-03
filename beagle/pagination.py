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


def time_filter(model, query_params):
    if query_params.get('created_date.timedelta'):
        time_threshold = datetime.now() - timedelta(hours=int(query_params['created_date.timedelta']))
        queryset = model.objects.filter(created_date__gt=time_threshold).order_by('-created_date')
    elif query_params.get('created_date.gt') or query_params.get('created_date.lt'):
        if query_params.get('created_date.gt'):
            time_gt = datetime.fromtimestamp(int(query_params['created_date.gt']))
            queryset = model.objects.filter(created_date__gt=time_gt).order_by('-created_date')
        if query_params.get('created_date.lt'):
            time_lt = datetime.fromtimestamp(int(query_params['created_date.lt']))
            queryset = model.objects.filter(created_date__lt=time_lt).order_by('-created_date')
    else:
        queryset = model.objects.order_by('-created_date').all()
    return queryset
