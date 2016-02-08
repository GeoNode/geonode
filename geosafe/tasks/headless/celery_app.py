# coding=utf-8
from celery import Celery

__author__ = 'Rizky Maulana Nugraha <lana.pcfre@gmail.com>'
__date__ = '1/28/16'


app = Celery('headless.tasks')
app.config_from_object('geosafe.tasks.headless.celeryconfig')
