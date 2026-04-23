from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """
    Allows access only to authenticated users with superadministrador role.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == 'superadministrador'
        )


class IsAdminUser(BasePermission):
    """
    Allows access to users with superadministrador or administrador role.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in ['superadministrador', 'administrador']
        )


class IsActive(BasePermission):
    """
    Allows access only if user is active.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.estado == 'activo'
        )
