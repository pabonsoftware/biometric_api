from __future__ import absolute_import, unicode_literals
import os 
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')

app = Celery('backend')

app.conf.beat_schedule={
    'vertificar_mantenimientos':{
        'task':'mantenimientos.tasks.vertificar_mantenimientos_periodicamente',
        'schedule':crontab(minute=0,hour=0)
    }
}

app.config_from_object('django.conf::settings',namespace='CELERY')

app.autodiscover_tasks()