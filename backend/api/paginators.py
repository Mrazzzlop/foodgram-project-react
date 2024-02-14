from rest_framework.pagination import PageNumberPagination

from foodgram.constants import PAGE_SIZE_PAGINATORS


class PageLimitPagination(PageNumberPagination):
    """A pagination class that limits the number of items per page."""
    page_size = PAGE_SIZE_PAGINATORS
    page_size_query_param = 'limit'
