import math
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
