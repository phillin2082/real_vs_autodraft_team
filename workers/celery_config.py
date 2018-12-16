import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')  # to work with windows

broker_url = 'redis://redis:6379/0'
backend_url = 'redis://redis:6379/1'
include = ['yahoo_fantasy_api.workers.tasks']
app = Celery('workers', broker=broker_url, backend=backend_url, include=include)


app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='America/Los_Angeles',
    #enable_utc=True,
)
