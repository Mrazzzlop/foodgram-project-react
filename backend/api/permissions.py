from rest_framework.permissions import SAFE_METHODS, BasePermission


class isAdminOrAuthorOrReadOnly(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(
            request.method in SAFE_METHODS
            or request.user
            and request.user.is_authenticated
            or request.user.is_staff
        )

    def has_object_permission(self, request, view, obj) -> bool:
        return bool(
            request.method in SAFE_METHODS
            or request.user.is_authenticated
            and obj.author == request.user
        )
