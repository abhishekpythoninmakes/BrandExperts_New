from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BrandExpertsEcommerce.settings')

app = Celery('BrandExpertsEcommerce')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# # Configure the daily cron job check
# app.conf.beat_schedule = {
#     'check-cron-jobs-daily': {
#         'task': 'pep_app.tasks.check_and_execute_cron_jobs',
#         'schedule': crontab(hour=8, minute=40),
#     },
# }

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')