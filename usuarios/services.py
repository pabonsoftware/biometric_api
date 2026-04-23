from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from .models import Usuario, UserAudit
from .selectors import get_admin_by_email
import logging

logger = logging.getLogger(__name__)


def login_usuario(correo, password):
    """Authenticate a user verifying they are active."""
    user = authenticate(username=correo, password=password)

    if user and user.estado != 'activo':
        logger.warning(f"Inactive user login attempt: {correo}")
        return None

    return user


def register_usuario(data):
    """Register a new user in the system."""
    password = data.pop("password")
    usuario = Usuario(**data)
    usuario.set_password(password)
    usuario.save()
    return usuario


@transaction.atomic
def create_admin(data: dict, actor: Usuario) -> Usuario:
    """
    Create a new admin in the system.

    Args:
        data: Dict with admin fields (nombre, correo, rol, estado)
        actor: SuperAdmin user performing the action

    Returns:
        Created user

    Raises:
        ValueError: If email already exists or invalid data
    """
    correo = data.get('correo', '').lower()

    if get_admin_by_email(correo):
        raise ValueError(f"El correo {correo} ya está registrado")

    password = data.pop('password', None)
    if not password:
        raise ValueError("La contraseña es requerida")

    usuario = Usuario(**data)
    usuario.set_password(password)
    usuario.save()

    # Record in audit
    UserAudit.objects.create(
        actor=actor,
        target_user=usuario,
        action_type='create',
        details={
            'nombre': usuario.nombre,
            'correo': usuario.correo,
            'rol': usuario.rol
        }
    )

    return usuario


@transaction.atomic
def edit_admin(user_id: int, data: dict, actor: Usuario) -> Usuario:
    """
    Edit existing admin information.

    Args:
        user_id: ID of the user to edit
        data: Dict with fields to update
        actor: SuperAdmin user performing the action

    Returns:
        Updated user

    Raises:
        Usuario.DoesNotExist: If user does not exist
        ValueError: If email already exists or invalid data
    """
    usuario = Usuario.objects.get(id=user_id)

    # Validate unique email if being modified
    if 'correo' in data and data['correo'] != usuario.correo:
        correo_new = data['correo'].lower()
        if get_admin_by_email(correo_new):
            raise ValueError(f"El correo {correo_new} ya está registrado")

    changes = {}
    for field, value in data.items():
        if field == 'password':
            usuario.set_password(value)
            changes['password'] = '***'
        else:
            if getattr(usuario, field) != value:
                changes[field] = value
            setattr(usuario, field, value)

    usuario.save()

    # Record in audit only if there were changes
    if changes:
        UserAudit.objects.create(
            actor=actor,
            target_user=usuario,
            action_type='edit',
            details=changes
        )

    return usuario


@transaction.atomic
def deactivate_admin(user_id: int, actor: Usuario) -> Usuario:
    """
    Deactivate an admin account.

    Args:
        user_id: ID of the user to deactivate
        actor: SuperAdmin user performing the action

    Returns:
        Deactivated user

    Raises:
        Usuario.DoesNotExist: If user does not exist
        ValueError: If user is already inactive or trying to deactivate self
    """
    usuario = Usuario.objects.get(id=user_id)

    if actor.id == usuario.id:
        raise ValueError("No puedes desactivar tu propia cuenta")

    if usuario.estado == 'inactivo':
        raise ValueError("El usuario ya está inactivo")

    usuario.estado = 'inactivo'
    usuario.save()

    # Record in audit
    UserAudit.objects.create(
        actor=actor,
        target_user=usuario,
        action_type='deactivate',
        details={'reason': 'Account deactivation by superadmin'}
    )

    return usuario


@transaction.atomic
def activate_admin(user_id: int, actor: Usuario) -> Usuario:
    """
    Reactivate a previously deactivated admin account.

    Args:
        user_id: ID of the user to activate
        actor: SuperAdmin user performing the action

    Returns:
        Activated user

    Raises:
        Usuario.DoesNotExist: If user does not exist
        ValueError: If user is already active
    """
    usuario = Usuario.objects.get(id=user_id)

    if usuario.estado == 'activo':
        raise ValueError("El usuario ya está activo")

    usuario.estado = 'activo'
    usuario.save()

    # Record in audit
    UserAudit.objects.create(
        actor=actor,
        target_user=usuario,
        action_type='activate',
        details={'reason': 'Account reactivation by superadmin'}
    )

    return usuario


def send_alert_email(recipient: str, message: str):
    """Send a notification email."""
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST:
        logger.warning(
            "Email not sent to %s: SMTP credentials are not configured.", recipient
        )
        return

    try:
        send_mail(
            "Notificación de Email",
            message,
            settings.EMAIL_HOST_USER,
            [recipient],
            fail_silently=False,
        )
    except Exception as e:
        logger.error("Failed to send email to %s: %s", recipient, e)