from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_admin(user) -> bool:
    """Only active staff accounts may use the admin panel."""
    return bool(user and user.is_authenticated and user.is_active and user.is_staff)


class IsStaff(BasePermission):
    message = "Bu amal uchun administrator huquqi kerak."

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsStaffOrReadOnly(BasePermission):
    """Anyone can read published content; only staff can change it."""

    message = "Bu amal uchun administrator huquqi kerak."

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_admin(request.user)


class IsSuperuser(BasePermission):
    """Administrators (superusers). Editors (staff only) manage content but not inbox/settings/accounts."""

    message = "Bu bo‘lim faqat administratorlar uchun."

    def has_permission(self, request, view):
        return is_admin(request.user) and request.user.is_superuser

