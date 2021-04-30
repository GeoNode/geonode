# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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

import uuid
import logging
import geoserver

from geoserver.catalog import ConflictingDataError, UploadError
from geoserver.resource import FeatureType, Coverage

from django.conf import settings

from geonode import GeoNodeException
from geonode.layers.utils import layer_type, get_files
from .helpers import (GEOSERVER_LAYER_TYPES,
                      gs_catalog,
                      get_store,
                      get_sld_for,
                      ogc_server_settings,
                      _create_db_featurestore,
                      _create_featurestore,
                      _create_coveragestore)

logger = logging.getLogger(__name__)


def geoserver_layer_type(filename):
    the_type = layer_type(filename)
    return GEOSERVER_LAYER_TYPES[the_type]


def geoserver_upload(
        layer,
        base_file,
        user,
        name,
        overwrite=True,
        title=None,
        abstract=None,
        permissions=None,
        keywords=(),
        charset='UTF-8'):

    # Step 2. Check that it is uploading to the same resource type as
    # the existing resource
    logger.debug('>>> Step 2. Make sure we are not trying to overwrite a '
                 'existing resource named [%s] with the wrong type', name)
    the_layer_type = geoserver_layer_type(base_file)

    # Get a short handle to the gsconfig geoserver catalog
    cat = gs_catalog

    # Ahmed Nour: get workspace by name instead of get default one.
    workspace = cat.get_workspace(settings.DEFAULT_WORKSPACE)
    # Check if the store exists in geoserver
    try:
        store = get_store(cat, name, workspace=workspace)
    except geoserver.catalog.FailedRequestError:
        # There is no store, ergo the road is clear
        pass
    else:
        # If we get a store, we do the following:
        resources = cat.get_resources(names=[name], stores=[store], workspaces=[workspace])

        if len(resources) > 0:
            # If our resource is already configured in the store it needs
            # to have the right resource type
            for resource in resources:
                if resource.name == name:
                    msg = 'Name already in use and overwrite is False'
                    assert overwrite, msg
                    existing_type = resource.resource_type
                    if existing_type != the_layer_type:
                        msg = f'Type of uploaded file {name} ({the_layer_type}) does not match type of existing resource type {existing_type}'
                        logger.debug(msg)
                        raise GeoNodeException(msg)

    # Step 3. Identify whether it is vector or raster and which extra files
    # are needed.
    logger.debug('>>> Step 3. Identifying if [%s] is vector or raster and '
                 'gathering extra files', name)
    if the_layer_type == FeatureType.resource_type:
        logger.debug('Uploading vector layer: [%s]', base_file)
        if ogc_server_settings.DATASTORE:
            create_store_and_resource = _create_db_featurestore
        else:
            create_store_and_resource = _create_featurestore
    elif the_layer_type == Coverage.resource_type:
        logger.debug("Uploading raster layer: [%s]", base_file)
        create_store_and_resource = _create_coveragestore
    else:
        msg = f'The layer type for name {name} is {the_layer_type}. It should be {FeatureType.resource_type} or {Coverage.resource_type},'
        logger.warn(msg)
        raise GeoNodeException(msg)

    # Step 4. Create the store in GeoServer
    logger.debug('>>> Step 4. Starting upload of [%s] to GeoServer...', name)

    # Get the helper files if they exist
    files = get_files(base_file)
    data = files
    if 'shp' not in files:
        data = base_file
    try:
        store, gs_resource = create_store_and_resource(
            name,
            data,
            charset=charset,
            overwrite=overwrite,
            workspace=workspace)
    except UploadError as e:
        msg = f'Could not save the layer {name}, there was an upload error: {str(e)}'
        logger.warn(msg)
        e.args = (msg,)
        raise
    except ConflictingDataError as e:
        # A datastore of this name already exists
        msg = ('GeoServer reported a conflict creating a store with name %s: '
               '"%s". This should never happen because a brand new name '
               'should have been generated. But since it happened, '
               'try renaming the file or deleting the store in '
               'GeoServer.' % (name, str(e)))
        logger.warn(msg)
        e.args = (msg,)
        raise
    else:
        logger.debug('Finished upload of [%s] to GeoServer without '
                     'errors.', name)

    # Step 5. Create the resource in GeoServer
    logger.debug('>>> Step 5. Generating the metadata for [%s] after '
                 'successful import to GeoSever', name)

    # Verify the resource was created
    if not gs_resource:
        gs_resource = gs_catalog.get_resource(
            name=name,
            workspace=workspace)

    if not gs_resource:
        msg = f'GeoNode encountered problems when creating layer {name}.It cannot find the Layer that matches this Workspace.try renaming your files.'
        logger.warn(msg)
        raise GeoNodeException(msg)

    assert gs_resource.name == name

    # Step 6. Make sure our data always has a valid projection
    logger.debug(f'>>> Step 6. Making sure [{name}] has a valid projection')
    _native_bbox = None
    try:
        _native_bbox = gs_resource.native_bbox
    except Exception:
        pass

    if _native_bbox and len(_native_bbox) >= 5 and _native_bbox[4:5][0] == 'EPSG:4326':
        box = _native_bbox[:4]
        minx, maxx, miny, maxy = [float(a) for a in box]
        if -180 <= round(minx, 5) <= 180 and -180 <= round(maxx, 5) <= 180 and \
                -90 <= round(miny, 5) <= 90 and -90 <= round(maxy, 5) <= 90:
            gs_resource.latlon_bbox = _native_bbox
            gs_resource.projection = "EPSG:4326"
        else:
            logger.warning('BBOX coordinates outside normal EPSG:4326 values for layer '
                           '[%s].', name)
            _native_bbox = [-180, -90, 180, 90, "EPSG:4326"]
            gs_resource.latlon_bbox = _native_bbox
            gs_resource.projection = "EPSG:4326"
            logger.debug('BBOX coordinates forced to [-180, -90, 180, 90] for layer [%s].', name)

    # Step 7. Create the style and assign it to the created resource
    logger.debug(f'>>> Step 7. Creating style for [{name}]')
    cat.save(gs_resource)
    publishing = cat.get_layer(name) or gs_resource
    sld = None
    try:
        if 'sld' in files:
            with open(files['sld'], 'rb') as f:
                sld = f.read()
        else:
            sld = get_sld_for(cat, layer)
    except Exception as e:
        logger.exception(e)

    style = None
    if sld:
        try:
            style = cat.get_style(name, workspace=workspace)
        except geoserver.catalog.FailedRequestError:
            style = cat.get_style(name)

        try:
            overwrite = style or False
            cat.create_style(name, sld, overwrite=overwrite, raw=True, workspace=workspace)
            cat.reset()
        except geoserver.catalog.ConflictingDataError as e:
            msg = f'There was already a style named {name}_layer in GeoServer, try to use: "{str(e)}"'
            logger.warn(msg)
            e.args = (msg,)
        except geoserver.catalog.UploadError as e:
            msg = f'Error while trying to upload style named {name}_layer in GeoServer, try to use: "{str(e)}"'
            e.args = (msg,)
            logger.exception(e)

        if style is None:
            try:
                style = cat.get_style(name, workspace=workspace) or cat.get_style(name)
            except Exception as e:
                style = cat.get_style('point')
                msg = f'Could not find any suitable style in GeoServer for Layer: "{name}"'
                e.args = (msg,)
                logger.exception(e)

        if style:
            publishing.default_style = style
            logger.debug('default style set to %s', name)
            try:
                cat.save(publishing)
            except geoserver.catalog.FailedRequestError as e:
                msg = f'Error while trying to save resource named {publishing} in GeoServer, try to use: "{str(e)}"'
                e.args = (msg,)
                logger.exception(e)

    # Step 8. Create the Django record for the layer
    logger.debug('>>> Step 8. Creating Django record for [%s]', name)
    alternate = f"{workspace.name}:{gs_resource.name}"
    layer_uuid = str(uuid.uuid1())

    defaults = dict(store=gs_resource.store.name,
                    storeType=gs_resource.store.resource_type,
                    alternate=alternate,
                    title=title or gs_resource.title,
                    uuid=layer_uuid,
                    abstract=abstract or gs_resource.abstract or '',
                    owner=user)

    return name, workspace.name, defaults, gs_resource
