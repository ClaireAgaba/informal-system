from rest_framework.pagination import PageNumberPagination


class FlexiblePagination(PageNumberPagination):
    """
    Custom pagination that allows clients to request larger page sizes.
    Default is 20, max is 1000.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000
