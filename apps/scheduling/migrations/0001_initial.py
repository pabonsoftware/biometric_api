import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("equipment", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MaintenanceSchedule",
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
                    "kind",
                    models.CharField(
                        choices=[
                            ("PREVENTIVE", "Mantenimiento preventivo"),
                            ("REPAIR", "Reparación programada"),
                        ],
                        db_index=True,
                        max_length=20,
                        verbose_name="Tipo",
                    ),
                ),
                (
                    "scheduled_date",
                    models.DateField(db_index=True, verbose_name="Fecha programada"),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Notas")),
                (
                    "notified_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Notificado el"
                    ),
                ),
                (
                    "is_completed",
                    models.BooleanField(
                        db_index=True, default=False, verbose_name="Completado"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Creado"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Actualizado"),
                ),
                (
                    "equipment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="schedules",
                        to="equipment.equipment",
                        verbose_name="Equipo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Agendamiento de mantenimiento",
                "verbose_name_plural": "Agendamientos de mantenimiento",
                "ordering": ["scheduled_date"],
            },
        ),
        migrations.AddIndex(
            model_name="maintenanceschedule",
            index=models.Index(
                fields=["equipment", "scheduled_date"], name="sched_eq_date_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="maintenanceschedule",
            index=models.Index(
                fields=["scheduled_date", "is_completed"], name="sched_date_comp_idx"
            ),
        ),
    ]
