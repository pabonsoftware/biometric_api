from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FailuresConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.failures"
    verbose_name = _("Reportes de falla")
