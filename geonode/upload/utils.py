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
import os
import re
import logging

from zipfile import ZipFile

from django.conf import settings

from geonode.geoserver.uploader.uploader import Uploader
from geonode.layers.models import Layer
from geonode.utils import _user, _password
from geoserver.catalog import FailedRequestError


def gs_uploader():
    url = "%srest" % settings.GEOSERVER_BASE_URL
    return Uploader(url, _user, _password)


def get_upload_type(filename):
    # @todo - this is bad and all file handling should be fixed now 
    # (but I'm working on somethign else)!
    
    base_name, extension = os.path.splitext(filename)
    extension = extension[1:].lower()
    
    possible_types = set(('shp','csv','tif', 'kml'))
    
    if extension == 'zip':
        zf = ZipFile(filename, 'r')
        file_list = zf.namelist()
        zf.close()
        for f in file_list:
            _, ext = os.path.splitext(f)
            ext = ext[1:].lower()
            if ext in possible_types:
                return ext
        raise Exception('Could not find a supported upload type in %s' % file_list)
    else:
        assert extension in possible_types
        return extension


def find_file_re(base_file, regex):
    '''case-insensitive filter the directory containing base_file w/ regex'''
    dirname = os.path.dirname(base_file)
    return map(lambda f: os.path.join(dirname,f), 
               filter(re.compile(regex, re.I).match, os.listdir(dirname)))


def find_sld(base_file):
    '''work around assumption in get_files that sld will be named the same'''
    f = find_file_re(base_file, '.*\.sld')
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
    xml_unsafe = re.compile(r"(^[^a-zA-Z\._]+)|([^a-zA-Z\._0-9]+)")
    dirname = os.path.dirname(base_file)
    if ext == ".zip":
        zf = ZipFile(base_file, 'r')
        rename = False
        main_file = None
        for f in zf.namelist():
            name, ext = os.path.splitext(os.path.basename(f))
            if xml_unsafe.search(name):
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
        if not main_file: raise Exception(
                'Could not locate a shapefile or tif file')
        if rename:
            # dang, have to unpack and rename
            zf.extractall(dirname)
        zf.close()
        if rename:
            os.unlink(base_file)
            base_file = os.path.join(dirname, main_file)

    for f in os.listdir(dirname):
        safe = xml_unsafe.sub("_", f)
        if safe != f:
            os.rename(os.path.join(dirname, f), os.path.join(dirname, safe))

    return os.path.join(
        dirname,
        xml_unsafe.sub('_', os.path.basename(base_file))
    )
        

def create_geoserver_db_featurestore(store_type=None):
    cat = Layer.objects.gs_catalog
    # get or create datastore
    try:
        if store_type == 'geogit' and hasattr(settings, 'GEOGIT_DATASTORE_NAME') and settings.GEOGIT_DATASTORE_NAME:
            ds = cat.get_store(settings.GEOGIT_DATASTORE_NAME)
        elif settings.DB_DATASTORE_NAME:
            ds = cat.get_store(settings.DB_DATASTORE_NAME)
        else:
            return None
    except FailedRequestError:
        if store_type == 'geogit' and hasattr(settings, 'GEOGIT_DATASTORE_NAME') and settings.GEOGIT_DATASTORE_NAME:
            logging.info(
                'Creating target datastore %s' % settings.GEOGIT_DATASTORE_NAME)
            ds = cat.create_datastore(settings.GEOGIT_DATASTORE_NAME)
            ds.type = "GeoGIT"
            ds.connection_parameters.update(
                geogit_repository=settings.GEOGIT_DATASTORE_NAME,
                create="true")
            cat.save(ds)
            ds = cat.get_store(settings.GEOGIT_DATASTORE_NAME)
        else:
            logging.info(
                'Creating target datastore %s' % settings.DB_DATASTORE_NAME)
            ds = cat.create_datastore(settings.DB_DATASTORE_NAME)
            ds.connection_parameters.update(
                host=settings.DB_DATASTORE_HOST,
                port=settings.DB_DATASTORE_PORT,
                database=settings.DB_DATASTORE_DATABASE,
                user=settings.DB_DATASTORE_USER,
                passwd=settings.DB_DATASTORE_PASSWORD,
                dbtype=settings.DB_DATASTORE_TYPE)
            cat.save(ds)
            ds = cat.get_store(settings.DB_DATASTORE_NAME)

    return ds
