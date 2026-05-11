import django.core.validators
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Branch",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text=_("Nombre único de la sede."),
                        max_length=120,
                        unique=True,
                        verbose_name=_("Nombre"),
                    ),
                ),
                (
                    "address",
                    models.CharField(max_length=255, verbose_name=_("Dirección")),
                ),
                (
                    "city",
                    models.CharField(
                        db_index=True, max_length=80, verbose_name=_("Ciudad")
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        max_length=30,
                        validators=[
                            django.core.validators.RegexValidator(
                                message=_("El teléfono no tiene un formato válido."),
                                regex=r"^\+?[0-9\s\-()]{7,20}$",
                            )
                        ],
                        verbose_name=_("Teléfono"),
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True,
                        max_length=254,
                        verbose_name=_("Correo electrónico"),
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name=_("Activa")),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name=_("Creada")),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name=_("Actualizada")),
                ),
            ],
            options={
                "verbose_name": _("Sede"),
                "verbose_name_plural": _("Sedes"),
                "ordering": ["name"],
            },
        ),
        migrations.AddIndex(
            model_name="branch",
            index=models.Index(fields=["name"], name="branch_name_idx"),
        ),
        migrations.AddIndex(
            model_name="branch",
            index=models.Index(fields=["city"], name="branch_city_idx"),
        ),
        migrations.AddIndex(
            model_name="branch",
            index=models.Index(fields=["is_active"], name="branch_is_active_idx"),
        ),
    ]
