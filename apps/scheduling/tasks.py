from __future__ import annotations

from email.mime.image import MIMEImage
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

# Logo embebido como imagen inline (cid) — se ve sin depender de imágenes
# externas y sin que el cliente de correo las bloquee. El template HTML lo
# referencia con <img src="cid:{LOGO_CID}">.
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo-clinica.png"
LOGO_CID = "logo-clinica"


def _embed_logo(message: EmailMultiAlternatives) -> None:
    """Adjunta el logo de la clínica como imagen inline en el correo."""
    try:
        logo_bytes = LOGO_PATH.read_bytes()
    except OSError:
        return  # Sin logo el correo sigue siendo válido; no se interrumpe el envío.
    # multipart/related agrupa el HTML con la imagen para que el cid resuelva.
    message.mixed_subtype = "related"
    logo = MIMEImage(logo_bytes, _subtype="png")
    logo.add_header("Content-ID", f"<{LOGO_CID}>")
    logo.add_header("Content-Disposition", "inline", filename="logo-clinica.png")
    message.attach(logo)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_schedule_notification(self, schedule_id: int) -> str:
    from .models import MaintenanceSchedule

    try:
        schedule = (
            MaintenanceSchedule.objects.select_related(
                "equipment",
                "equipment__branch",
                "assigned_engineer",
                "assigned_technician",
            ).get(pk=schedule_id)
        )
    except MaintenanceSchedule.DoesNotExist:
        return "schedule_not_found"

    equipment = schedule.equipment
    branch = equipment.branch

    recipients = list(getattr(settings, "MAINTENANCE_NOTIFICATION_EMAILS", []) or [])
    if branch.email:
        recipients.append(branch.email)
    if schedule.assigned_engineer and schedule.assigned_engineer.email:
        recipients.append(schedule.assigned_engineer.email)
    if schedule.assigned_technician and schedule.assigned_technician.email:
        recipients.append(schedule.assigned_technician.email)
    recipients = list({r for r in recipients if r})
    if not recipients:
        return "no_recipients"

    context = {
        "schedule": schedule,
        "equipment": equipment,
        "branch": branch,
    }
    subject = (
        f"[Biometric] Mantenimiento programado: {equipment.asset_tag} "
        f"({schedule.scheduled_date.isoformat()})"
    )
    body_text = render_to_string("scheduling/email/schedule_notification.txt", context)
    body_html = render_to_string("scheduling/email/schedule_notification.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=body_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    message.attach_alternative(body_html, "text/html")
    _embed_logo(message)

    try:
        message.send(fail_silently=False)
    except Exception as exc:
        raise self.retry(exc=exc) from exc

    schedule.notified_at = timezone.now()
    schedule.save(update_fields=["notified_at", "updated_at"])
    return "sent"
