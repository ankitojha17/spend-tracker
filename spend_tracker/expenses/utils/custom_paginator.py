from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPaginator(PageNumberPagination):
    """
    Standard page-number pagination. Client can override the page size with
    ?page_size=, capped at max_page_size so nobody can request the entire
    table in one call.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })
