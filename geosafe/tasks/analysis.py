# coding=utf-8
import logging
import os
import time
import urllib
import urlparse
from zipfile import ZipFile

from celery.app import shared_task
from django.conf import settings
from django.core.urlresolvers import reverse

from geonode.layers.models import Layer
from geonode.layers.utils import file_upload
from geosafe.models import Analysis, Metadata
from geosafe.tasks.headless.analysis import read_keywords_iso_metadata

__author__ = 'lucernae'


LOGGER = logging.getLogger(__name__)


@shared_task(
    name='geosafe.tasks.analysis.create_metadata_object',
    queue='geosafe')
def create_metadata_object(layer_id):
    # Sleep 5 second to let layer post_save ends
    time.sleep(5)
    metadata = Metadata()
    layer = Layer.objects.get(id=layer_id)
    metadata.layer = layer
    layer_url = reverse(
        'geosafe:layer-metadata',
        kwargs={'layer_id': layer_id})
    layer_url = urlparse.urljoin(settings.GEONODE_BASE_URL, layer_url)
    async_result = read_keywords_iso_metadata.delay(
        layer_url, 'layer_purpose')
    metadata.layer_purpose = async_result.get()
    metadata.save()


@shared_task(
    name='geosafe.tasks.analysis.process_impact_result',
    queue='geosafe')
def process_impact_result(analysis_id, impact_url_result):
    # wait for process to return the result
    impact_url = impact_url_result.get()
    analysis = Analysis.objects.get(id=analysis_id)
    # download impact zip
    impact_path, _ = urllib.urlretrieve(impact_url)
    dir_name = os.path.dirname(impact_path)
    with ZipFile(impact_path) as zf:
        zf.extractall(path=dir_name)
        for name in zf.namelist():
            _, ext = os.path.splitext(name)
            if ext in ['.shp', '.tif']:
                saved_layer = file_upload(
                    os.path.join(dir_name, name),
                    overwrite=True)
                saved_layer.set_default_permissions()
                analysis.impact_layer = saved_layer
                analysis.save(run_analysis_flag=False)
                break
