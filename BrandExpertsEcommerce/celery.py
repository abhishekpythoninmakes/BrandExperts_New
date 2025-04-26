from __future__ import absolute_import, unicode_literals
from celery.schedules import crontab
import os

from django.conf import settings

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BrandExpertsEcommerce.settings')

app = Celery('BrandExpertsEcommerce')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')



# CELERY BEAT SETTINGS



# app.conf.beat_schedule = {
#     'send-daily-certificates': {
#         'task': 'Certificate_App.tasks.send_certificate_task',
#         'schedule': crontab(hour=0, minute=0),  # Run daily at midnight
#     },
# }


# Load task modules from all registered Django apps.



# Schedule the backup task
# app.conf.beat_schedule = {
#     'weekly-database-backup': {
#         'task': 'products_app.tasks.backup_database_and_send_email',
#         'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Sunday at 2 AM
#     },
# }

from celery.schedules import timedelta

# app.conf.beat_schedule = {
#     'database-backup-every-1m-2s': {
#         'task': 'products_app.tasks.backup_database_and_send_email',
#         'schedule': timedelta(seconds=62),  # 1 minute + 2 seconds
#     },
# }

# Add this to your existing celery.py file

# Add the cron job check task to the beat schedule
# Add this to your existing celery.py file

# Add the cron job check task to the beat schedule
# app.conf.beat_schedule = {
#     # Schedule the cron job check to run at 7:30 AM UTC every day
#     'check-cron-jobs-daily': {
#         'task': 'partner_app.tasks.check_and_execute_cron_jobs',
#         'schedule': crontab(hour=7, minute=30),  # Run at 7:30 AM UTC
#     },
# }

app.conf.beat_schedule = {
    'check-cron-jobs-daily': {
        'task': 'partner_app.tasks.check_and_execute_cron_jobs',
        'schedule': crontab(hour=10, minute=52),  # 10:52 AM UTC = 4:22 PM IST
    },
}



# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
