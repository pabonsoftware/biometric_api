from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import MaintenanceRecord


@receiver(pre_delete, sender=MaintenanceRecord)
def remove_pdf_file(sender, instance: MaintenanceRecord, **kwargs) -> None:
    """Borra el PDF asociado del storage al eliminar el registro."""
    if instance.pdf_file:
        instance.pdf_file.delete(save=False)
