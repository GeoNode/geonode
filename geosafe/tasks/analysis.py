# coding=utf-8
import logging
import os
import tempfile
import time
import urlparse
from zipfile import ZipFile

import requests
import shutil
from celery.app import shared_task
from django.conf import settings
from django.core.files.base import File
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q

from geonode.layers.models import Layer
from geonode.layers.utils import file_upload
from geosafe.models import Analysis, Metadata
from geosafe.tasks.headless.analysis import read_keywords_iso_metadata

__author__ = 'lucernae'


LOGGER = logging.getLogger(__name__)


def download_file(url):
    parsed_uri = urlparse.urlparse(url)
    if parsed_uri.scheme == 'http' or parsed_uri.scheme == 'https':
        tmpfile = tempfile.mktemp()
        # NOTE the stream=True parameter
        # Assign User-Agent to emulate browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) '
                          'Gecko/20071127 Firefox/2.0.0.11'
        }
        r = requests.get(url, headers=headers, stream=True)
        with open(tmpfile, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return tmpfile
    elif parsed_uri.scheme == 'file' or not parsed_uri.scheme:
        return parsed_uri.path


@shared_task(
    name='geosafe.tasks.analysis.create_metadata_object',
    queue='geosafe')
def create_metadata_object(layer_id):
    """Create metadata object of a given layer

    :param layer_id: layer ID
    :type layer_id: int

    :return: True if success
    :rtype: bool
    """
    # Sleep 5 second to let layer post_save ends
    # That way, the Layer can be accessed
    time.sleep(5)
    metadata = Metadata()
    layer = Layer.objects.get(id=layer_id)
    metadata.layer = layer
    layer_url = reverse(
        'geosafe:layer-metadata',
        kwargs={'layer_id': layer_id})
    layer_url = urlparse.urljoin(settings.GEONODE_BASE_URL, layer_url)
    async_result = read_keywords_iso_metadata.delay(
        layer_url, ('layer_purpose', 'hazard', 'exposure'))
    keywords = async_result.get()
    metadata.layer_purpose = keywords.get('layer_purpose', None)
    metadata.category = keywords.get(metadata.layer_purpose, None)
    metadata.save()
    return True


@shared_task(
    name='geosafe.tasks.analysis.clean_impact_result',
    queue='geosafe')
def clean_impact_result():
    """Clean all the impact results not marked kept

    :return:
    """
    query = Q(keep=True)
    for a in Analysis.objects.filter(~query):
        a.delete()

    for i in Metadata.objects.filter(layer_purpose='impact'):
        try:
            Analysis.objects.get(impact_layer=i.layer)
        except Analysis.DoesNotExist:
            i.delete()


@shared_task(
    name='geosafe.tasks.analysis.process_impact_result',
    queue='geosafe')
def process_impact_result(analysis_id, impact_url_result):
    """Extract impact analysis after running it via InaSAFE-Headless celery

    :param analysis_id: analysis id of the object
    :type analysis_id: int

    :param impact_url_result: the AsyncResult taken from executing headless
        task to run impact analysis
    :type impact_url_result: celery.result.AsyncResult

    :return: True if success
    :rtype: bool
    """
    # wait for process to return the result
    impact_url = impact_url_result.get()
    analysis = Analysis.objects.get(id=analysis_id)
    # download impact zip
    impact_path = download_file(impact_url)
    dir_name = os.path.dirname(impact_path)
    success = False
    with ZipFile(impact_path) as zf:
        zf.extractall(path=dir_name)
        for name in zf.namelist():
            basename, ext = os.path.splitext(name)
            if ext in ['.shp', '.tif']:
                saved_layer = file_upload(
                    os.path.join(dir_name, name),
                    overwrite=True)
                saved_layer.set_default_permissions()
                layer_name = analysis.get_default_impact_title()
                saved_layer.title = layer_name
                saved_layer.save()
                current_impact = None
                if analysis.impact_layer:
                    current_impact = analysis.impact_layer
                analysis.impact_layer = saved_layer

                # check map report and table
                report_map_path = os.path.join(
                    dir_name, '%s.pdf' % basename
                )

                if os.path.exists(report_map_path):
                    analysis.assign_report_map(report_map_path)

                report_table_path = os.path.join(
                    dir_name, '%s_table.pdf' % basename
                )

                if os.path.exists(report_table_path):
                    analysis.assign_report_table(report_table_path)

                analysis.save()

                if current_impact:
                    current_impact.delete()
                success = True
                break

        # cleanup
        for name in zf.namelist():
            filepath = os.path.join(dir_name, name)
            try:
                os.remove(filepath)
            except:
                pass

    # cleanup
    try:
        os.remove(impact_path)
    except:
        pass

    if not success:
        LOGGER.info('No impact layer found in %s' % impact_url)

    return success
