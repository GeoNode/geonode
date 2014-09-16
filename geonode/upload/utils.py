#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import logging
import os
import re
from django.conf import settings
from geonode.upload.files import _clean_string, SpatialFiles
from geoserver.catalog import FailedRequestError
from geonode.geoserver.helpers import ogc_server_settings, gs_catalog
from zipfile import ZipFile

logger = logging.getLogger(__name__)


def get_upload_type(filename):
    # @todo - this is bad and all file handling should be fixed now
    # (but I'm working on something else)!

    base_name, extension = os.path.splitext(filename)
    extension = extension[1:].lower()

    possible_types = set(('shp', 'csv', 'tif', 'kml'))

    if extension == 'zip':
        zf = ZipFile(filename, 'r')
        file_list = zf.namelist()
        zf.close()
        for f in file_list:
            _, ext = os.path.splitext(f)
            ext = ext[1:].lower()
            if ext in possible_types:
                return ext
        raise Exception(
            'Could not find a supported upload type in %s' %
            file_list)
    else:
        assert extension in possible_types
        return extension


def find_file_re(base_file, regex):
    """
    Returns files in the same directory as the base_file that match the regular expression
    """

    dirname = os.path.dirname(base_file)
    return map(lambda f: os.path.join(dirname, f),
               filter(re.compile(regex, re.I).match, os.listdir(dirname)))


def find_sld(base_file):
    """
    Returns files in same directory as base_file that end in .sld
    """

    if isinstance(base_file, SpatialFiles):
        base_file = base_file.dirname
        logger.debug(base_file)

    f = find_file_re(base_file, '.*\.sld')
    logger.debug('slds: {}'.format(f))
    return f[0] if f else None


def rename_and_prepare(base_file):
    """ensure the file(s) have a proper name @hack this should be done
    in a nicer way, but needs fixing now To fix longer term: if
    geonode computes a name, the uploader should respect it As it
    is/was, geonode will compute a name based on the zipfile but the
    importer will use names as it unpacks the zipfile. Renaming all
    the various pieces seems a burden on the client

    Additionally, if a SLD file is present, extract this.
    """
    name, ext = os.path.splitext(os.path.basename(base_file))
    dirname = os.path.dirname(base_file)
    if ext == ".zip":
        zf = ZipFile(base_file, 'r')
        rename = False
        main_file = None
        for f in zf.namelist():
            name, ext = os.path.splitext(os.path.basename(f))
            if _clean_string(name) != name:
                rename = True
            # @todo other files - need to unify extension handling somewhere
            if ext.lower() == '.shp':
                main_file = f
            elif ext.lower() == '.tif':
                main_file = f
            elif ext.lower() == '.csv':
                main_file = f

            # if an sld is there, extract so it can be found
            if ext.lower() == '.sld':
                zf.extract(f, dirname)
        if not main_file:
            raise Exception('Could not locate a shapefile or tif file')
        if rename:
            # dang, have to unpack and rename
            zf.extractall(dirname)
        zf.close()
        if rename:
            os.unlink(base_file)
            base_file = os.path.join(dirname, main_file)

    for f in os.listdir(dirname):
        safe = _clean_string(f)
        if safe != f:
            os.rename(os.path.join(dirname, f), os.path.join(dirname, safe))

    return os.path.join(
        dirname,
        _clean_string(os.path.basename(base_file))
    )


def create_geoserver_db_featurestore(store_type=None, store_name=None):
    cat = gs_catalog
    dsname = ogc_server_settings.DATASTORE
    # get or create datastore
    try:
        if store_type == 'geogit' and ogc_server_settings.GEOGIT_ENABLED:
            if store_name is not None:
                ds = cat.get_store(store_name)
            else:
                ds = cat.get_store(settings.GEOGIT_DATASTORE_NAME)
        elif dsname:
            ds = cat.get_store(dsname)
        else:
            return None
    except FailedRequestError:
        if store_type == 'geogit':
            if store_name is None and hasattr(
                    settings,
                    'GEOGIT_DATASTORE_NAME'):
                store_name = settings.GEOGIT_DATASTORE_NAME
            logger.info(
                'Creating target datastore %s' %
                settings.GEOGIT_DATASTORE_NAME)
            ds = cat.create_datastore(store_name)
            ds.type = "GeoGIT"
            ds.connection_parameters.update(
                geogit_repository=os.path.join(
                    ogc_server_settings.GEOGIT_DATASTORE_DIR,
                    store_name),
                branch="master",
                create="true")
            cat.save(ds)
            ds = cat.get_store(store_name)
        else:
            logging.info(
                'Creating target datastore %s' % dsname)
            ds = cat.create_datastore(dsname)
            db = ogc_server_settings.datastore_db
            ds.connection_parameters.update(
                host=db['HOST'],
                port=db['PORT'],
                database=db['NAME'],
                user=db['USER'],
                passwd=db['PASSWORD'],
                dbtype='postgis')
            cat.save(ds)
            ds = cat.get_store(dsname)

    return ds
