"""
Custom permission classes for maintenance operations.

Implements role-based access control for maintenance management according to user roles.
"""

from rest_framework.permissions import BasePermission


class IsIngenieroBiomedico(BasePermission):
    """
    Allows access only to authenticated users with ingenierobiomedico role.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == 'ingenierobiomedico'
        )


class IsTecnicoBiomedico(BasePermission):
    """
    Allows access only to authenticated users with tecnicobiomedico role.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == 'tecnicobiomedico'
        )


class IsIngenierOrTecnico(BasePermission):
    """
    Allows access to users with ingenierobiomedico or tecnicobiomedico role.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in ['ingenierobiomedico', 'tecnicobiomedico']
        )


class IsCreatorOrAdmin(BasePermission):
    """
    Allows access if user is the creator of the maintenance record or is an admin/superadmin.
    Object-level permission to check if the user created the maintenance.
    """

    def has_object_permission(self, request, view, obj):
        # Admin/superadmin can always edit
        if request.user.rol in ['superadministrador', 'administrador']:
            return True

        # Creator can edit their own maintenance
        return obj.responsable == request.user


class IsAuthenticatedAndActive(BasePermission):
    """
    Allows access only if user is authenticated and active.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.estado == 'activo'
        )


class CanApproveOrSupervise(BasePermission):
    """
    Allows access only to coordinador, administrador, or superadministrador.
    Used for approval and supervision actions.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in [
                'coordinador',
                'administrador',
                'superadministrador'
            ]
        )


class CanViewMaintenance(BasePermission):
    """
    Allows access to view maintenance if:
    - User is admin/superadmin (can view all)
    - User is the responsible/creator
    - User is in approval/coordination role
    """

    def has_object_permission(self, request, view, obj):
        # Admin can view all
        if request.user.rol in ['superadministrador', 'administrador']:
            return True

        # Creator/responsible can view
        if obj.responsable == request.user:
            return True

        # Coordinador and above can view all
        if request.user.rol in ['coordinador']:
            return True

        return False
