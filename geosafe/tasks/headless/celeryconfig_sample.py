# coding=utf-8
"""Sample file configuration for celery_app worker

This file is intended only for a sample.
Please copy it as celeryconfig.py so it can be read
"""

__author__ = 'Rizky Maulana Nugraha <lana.pcfre@gmail.com>'
__date__ = '1/28/16'


BROKER_URL = 'redis://localhost:6379/0'

CELERY_RESULT_BACKEND = BROKER_URL

CELERY_ROUTES = {
    'headless.tasks.inasafe_wrapper': {
        'queue': 'inasafe-headless'
    }
}
