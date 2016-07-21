# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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
from django.conf import settings
from geoserver.catalog import FailedRequestError
from geonode.geoserver.helpers import ogc_server_settings, gs_catalog
from simplejson import dumps
from geoserver.store import UnsavedDataStore

logger = logging.getLogger(__name__)


class UnsavedGeogigDataStore(UnsavedDataStore):
    save_method = "PUT"

    def __init__(self, catalog, name, workspace, author_name, author_email):
        self.author_name = author_name
        self.author_email = author_email
        super(UnsavedGeogigDataStore, self).__init__(catalog, name, workspace)

    def message(self):
        message = {
            "authorName": self.author_name,
            "authorEmail": self.author_email
        }
        if settings.OGC_SERVER['default']['PG_GEOGIG'] is True:
            datastore = settings.OGC_SERVER['default']['DATASTORE']
            pg_geogig_db = settings.DATABASES[datastore]
            message["dbHost"] = pg_geogig_db['HOST']
            message["dbPort"] = pg_geogig_db['PORT'] or '5432'
            message["dbName"] = pg_geogig_db['NAME']
            message["dbSchema"] = pg_geogig_db['SCHEMA']
            message["dbUser"] = pg_geogig_db['USER']
            message["dbPassword"] = pg_geogig_db['PASSWORD']
        else:
            message["parentDirectory"] = \
                ogc_server_settings.GEOGIG_DATASTORE_DIR
        return dumps(message)

    @property
    def href(self):
        return ("%sgeogig/repos/%s/init.json"
                % (ogc_server_settings.LOCATION, self.name))


def create_geoserver_db_featurestore(
        store_type=None, store_name=None,
        author_name='admin', author_email='admin@geonode.org'):
    cat = gs_catalog
    dsname = ogc_server_settings.DATASTORE
    # get or create datastore
    try:
        if store_type == 'geogig' and ogc_server_settings.GEOGIG_ENABLED:
            if store_name is not None:
                ds = cat.get_store(store_name)
            else:
                ds = cat.get_store(settings.GEOGIG_DATASTORE_NAME)
        elif dsname:
            ds = cat.get_store(dsname)
        else:
            return None
    except FailedRequestError:
        if store_type == 'geogig':
            ds = UnsavedGeogigDataStore(
                cat, store_name, cat.get_default_workspace(),
                author_name, author_email)
            cat.save(ds)
            ds = cat.get_store(store_name)
        else:
            logging.info(
                'Creating target datastore %s' % dsname)
            ds = cat.create_datastore(dsname)
            db = ogc_server_settings.datastore_db
            ds.connection_parameters.update(
                host=db['HOST'],
                port=db['PORT'] if isinstance(
                    db['PORT'], basestring) else str(db['PORT']) or '5432',
                database=db['NAME'],
                user=db['USER'],
                passwd=db['PASSWORD'],
                dbtype='postgis')
            cat.save(ds)
            ds = cat.get_store(dsname)
            assert ds.enabled

    return ds
