from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import MaintenanceSchedule
from .tasks import send_schedule_notification


@receiver(post_save, sender=MaintenanceSchedule)
def trigger_schedule_notification(sender, instance: MaintenanceSchedule, created: bool, **kwargs):
    if created:
        send_schedule_notification.delay(instance.pk)
