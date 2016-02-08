# coding=utf-8
import logging
from geosafe.tasks.headless.celery_app import app


__author__ = 'Rizky Maulana Nugraha <lana.pcfre@gmail.com>'
__date__ = '2/3/16'


LOGGER = logging.getLogger(__name__)


@app.task(
    name='headless.tasks.inasafe_wrapper.filter_impact_function',
    queue='inasafe-headless')
def filter_impact_function(hazard=None, exposure=None):
    """Proxy tasks for celery broker"""
    LOGGER.info('This function is intended to be executed by celery task')


@app.task(
    name='headless.tasks.inasafe_wrapper.run_analysis',
    queue='inasafe-headless')
def run_analysis(hazard, exposure, function, aggregation=None,
                 generate_report=False):
    """Proxy tasks for celery broker"""
    LOGGER.info('This function is intended to be executed by celery task')


@app.task(
    name='headless.tasks.inasafe_wrapper.read_keywords_iso_metadata',
    queue='inasafe-headless')
def read_keywords_iso_metadata(metadata_url, keyword=None):
    """Proxy tasks for celery broker"""
    LOGGER.info('This function is intended to be executed by celery task')
