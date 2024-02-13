from rest_framework.pagination import PageNumberPagination

from foodgram.constants import PAGE_SIZE_PAGINATORS


class PageLimitPagination(PageNumberPagination):
    """
    A pagination class that limits the number of items per page.

    Attributes:
        page_size (int): The number of items per page.
        page_size_query_param (str): The query parameter
        name for specifying the page size.

    """
    page_size = PAGE_SIZE_PAGINATORS
    page_size_query_param = 'limit'
