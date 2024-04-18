from __future__ import absolute_import, unicode_literals
import os

from celery import Celery
from django.conf import settings
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_celery_project.settings')

app = Celery('django_celery_project')
app.conf.enable_utc = False

app.conf.update(timezone = 'America/Monterrey')

app.config_from_object(settings, namespace='CELERY')

# Celery Beat Settings
# app.conf.beat_schedule = {
#     'send-mail-every-day-at-8': {
#         'task': 'tasks_app.tasks.periodic_task',
#         'schedule': crontab(hour=15, minute=10, day_of_month=3, month_of_year = 4),
#         #'args': (2,)
#     }
    
# }

# Celery Schedules - https://docs.celeryproject.org/en/stable/reference/celery.schedules.html

app.autodiscover_tasks(['tasks_app'], force=True)

# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')