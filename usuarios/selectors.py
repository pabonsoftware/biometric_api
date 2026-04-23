from django.db.models import QuerySet
from .models import Usuario, UserAudit


def get_admins() -> QuerySet:
    """
    Get all administrators (superadministrador and administrador).
    Optimized to avoid N+1 queries.
    """
    return Usuario.objects.filter(
        rol__in=['superadministrador', 'administrador']
    ).order_by('-date_joined')


def get_admin_by_id(user_id: int):
    """Get a specific admin by ID."""
    return Usuario.objects.filter(
        id=user_id,
        rol__in=['superadministrador', 'administrador']
    ).first()


def get_admin_by_email(email: str):
    """Get a specific admin by email."""
    return Usuario.objects.filter(
        correo=email,
        rol__in=['superadministrador', 'administrador']
    ).first()


def get_active_admins() -> QuerySet:
    """Get only active admins."""
    return get_admins().filter(estado='activo')


def get_inactive_admins() -> QuerySet:
    """Get only inactive admins."""
    return get_admins().filter(estado='inactivo')


def get_user_audit_log(user_id: int) -> QuerySet:
    """Get the audit log for a specific user."""
    return UserAudit.objects.filter(
        target_user_id=user_id
    ).select_related('actor', 'target_user')


def get_audit_log_by_action(action_type: str) -> QuerySet:
    """Get audit logs filtered by action type."""
    return UserAudit.objects.filter(
        action_type=action_type
    ).select_related('actor', 'target_user').order_by('-created_at')
