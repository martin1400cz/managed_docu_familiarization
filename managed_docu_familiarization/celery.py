from celery.signals import setup_logging
import os

from logging.config import dictConfig
from django.conf import settings

from celery import Celery

# all settings based on this article
# https://docs.celeryq.dev/en/v5.2.6/django/first-steps-with-django.html

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

app = Celery('managed_docu_familiarization')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# import logging settings from Django
@setup_logging.connect
def config_loggers(*args, **kwargs):
    dictConfig(settings.LOGGING)

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


class TaskWarning(Exception):
    pass
