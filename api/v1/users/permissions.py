from django.utils.translation import gettext_lazy as _
from rest_framework import permissions

from apps.users.models import User


class IsAdminRole(permissions.BasePermission):
    """Permite el acceso a usuarios con rol superadmin o admin."""

    message = _("No tienes permisos para esta acción.")

    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(
            u
            and u.is_authenticated
            and u.role in {User.Role.SUPERADMIN, User.Role.ADMIN}
        )

    def has_object_permission(self, request, view, obj) -> bool:
        return self.has_permission(request, view)


class IsSelf(permissions.BasePermission):
    """Permite el acceso solo si el objeto es el propio usuario autenticado."""

    message = _("No tienes permisos para esta acción.")

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        return obj.pk == request.user.pk
