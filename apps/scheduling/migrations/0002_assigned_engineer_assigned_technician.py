import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scheduling", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="maintenanceschedule",
            name="assigned_engineer",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"is_active": True, "role": "ingeniero"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="engineering_schedules",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Ingeniero asignado",
            ),
        ),
        migrations.AddField(
            model_name="maintenanceschedule",
            name="assigned_technician",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"is_active": True, "role": "tecnico"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="technician_schedules",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Técnico asignado",
            ),
        ),
        migrations.AddIndex(
            model_name="maintenanceschedule",
            index=models.Index(fields=["assigned_engineer"], name="sched_engineer_idx"),
        ),
        migrations.AddIndex(
            model_name="maintenanceschedule",
            index=models.Index(fields=["assigned_technician"], name="sched_technician_idx"),
        ),
    ]
