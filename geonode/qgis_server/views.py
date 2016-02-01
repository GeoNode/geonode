__author__ = 'ismailsunni'
__project_name__ = 'geonode'
__filename__ = 'views'
__date__ = '1/29/16'
__copyright__ = 'imajimatika@gmail.com'


import os
import logging
import zipfile
import StringIO

from django.http import HttpResponse
from django.db.models import ObjectDoesNotExist
from geonode.layers.models import Layer
from geonode.qgis_server.models import QGISServerLayer

logger = logging.getLogger('geonode.qgis_server.views')

def download_zip(request, layername):
    try:
        layer = Layer.objects.get(name=layername)
    except ObjectDoesNotExist:
        logger.debug('No layer found for %s' % layername)
        return

    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except ObjectDoesNotExist:
        logger.debug('No QGIS Server Layer for existing layer %s' % layername)
        return

    basename, _ = os.path.splitext(qgis_layer.base_layer_path)
    # Files (local path) to put in the .zip
    filenames = []
    for ext in QGISServerLayer.accepted_format:
        target_file = basename + '.' + ext
        if os.path.exists(target_file):
            filenames.append(target_file)

    # Folder name in ZIP archive which contains the above files
    # E.g [thearchive.zip]/somefiles/file2.txt
    zip_subdir = layer.name
    zip_filename = "%s.zip" % zip_subdir

    # Open StringIO to grab in-memory ZIP contents
    s = StringIO.StringIO()

    # The zip compressor
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        logger.debug('fpath: %s' % fpath)
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        logger.debug('fdir: %s' % fdir)
        logger.debug('fname: %s' % fname)

        zip_path = os.path.join(zip_subdir, fname)
        logger.debug('zip_path: %s' % zip_path)

        # Add file, at correct path
        zf.write(fpath, zip_path)

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = HttpResponse(s.getvalue(), mimetype = "application/x-zip-compressed")
    # ..and correct content-disposition
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return resp