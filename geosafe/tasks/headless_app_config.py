# coding=utf-8
import os

__author__ = 'Rizky Maulana Nugraha <lana.pcfre@gmail.com>'
__date__ = '1/28/16'


BROKER_URL = os.environ['INASAFE_HEADLESS_BROKER_HOST']

# CELERY_RESULT_BACKEND = 'db+postgresql://%s:%s@db/gis' % (
#     os.environ['INASAFE_HEADLESS_DB_USERNAME'],
#     os.environ['INASAFE_HEADLESS_DB_PASS'])
CELERY_RESULT_BACKEND = BROKER_URL

deploy_output_dir = os.environ['INASAFE_HEADLESS_DEPLOY_OUTPUT_DIR']
deploy_output_url = os.environ['INASAFE_HEADLESS_DEPLOY_OUTPUT_URL']

try:
    # Put site specific configuration in this module
    import celeryconfiglocal
except:
    pass
