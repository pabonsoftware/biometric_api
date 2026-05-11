from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import Equipment
from .services import generate_qr_for_equipment


@receiver(post_save, sender=Equipment)
def auto_generate_qr(sender, instance: Equipment, created: bool, **kwargs) -> None:
    if created and not instance.qr_code:
        generate_qr_for_equipment(instance)


@receiver(pre_delete, sender=Equipment)
def remove_qr_file(sender, instance: Equipment, **kwargs) -> None:
    if instance.qr_code:
        instance.qr_code.delete(save=False)
