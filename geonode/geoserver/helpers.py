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
from collections import namedtuple, defaultdict
import datetime
from decimal import Decimal
import errno
from itertools import cycle, izip
import json
import logging
import traceback
import os
from os.path import basename, splitext, isfile
import re
import sys
from threading import local
import time
import uuid

import urllib
from urlparse import urlsplit, urlparse, urljoin

from agon_ratings.models import OverallRating
from bs4 import BeautifulSoup
from dialogos.models import Comment
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import pre_delete
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext as _
from geoserver.catalog import Catalog, FailedRequestError
from geoserver.resource import FeatureType, Coverage
from geoserver.store import CoverageStore, DataStore, datastore_from_index, \
    coveragestore_from_index, wmsstore_from_index
from geoserver.support import DimensionInfo
from geoserver.workspace import Workspace
from gsimporter import Client
from lxml import etree
from owslib.wcs import WebCoverageService
from owslib.wms import WebMapService
from geonode import GeoNodeException
from geonode.base.auth import get_or_create_token
from geonode.utils import http_client
from geonode.layers.models import Layer, Attribute, Style
from geonode.layers.enumerations import LAYER_ATTRIBUTE_NUMERIC_DATA_TYPES
from geonode.security.views import _perms_info_json
from geonode.security.utils import set_geowebcache_invalidate_cache
import xml.etree.ElementTree as ET
from django.utils.module_loading import import_string


logger = logging.getLogger(__name__)

if not hasattr(settings, 'OGC_SERVER'):
    msg = (
        'Please configure OGC_SERVER when enabling geonode.geoserver.'
        ' More info can be found at '
        'http://docs.geonode.org/en/master/reference/developers/settings.html#ogc-server')
    raise ImproperlyConfigured(msg)


def check_geoserver_is_up():
    """Verifies all geoserver is running,
       this is needed to be able to upload.
    """
    url = "%s" % ogc_server_settings.LOCATION
    req, content = http_client.get(url)
    msg = ('Cannot connect to the GeoServer at %s\nPlease make sure you '
           'have started it.' % url)
    logger.debug(req)
    assert req.status_code == 200, msg


def _add_sld_boilerplate(symbolizer):
    """
    Wrap an XML snippet representing a single symbolizer in the appropriate
    elements to make it a valid SLD which applies that symbolizer to all features,
    including format strings to allow interpolating a "name" variable in.
    """
    return """
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>%(name)s</Name>
    <UserStyle>
    <Name>%(name)s</Name>
    <Title>%(name)s</Title>
      <FeatureTypeStyle>
        <Rule>
""" + symbolizer + """
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
"""


_raster_template = """
<RasterSymbolizer>
    <Opacity>1.0</Opacity>
</RasterSymbolizer>
"""

_polygon_template = """
<PolygonSymbolizer>
  <Fill>
    <CssParameter name="fill">%(bg)s</CssParameter>
  </Fill>
  <Stroke>
    <CssParameter name="stroke">%(fg)s</CssParameter>
    <CssParameter name="stroke-width">0.7</CssParameter>
  </Stroke>
</PolygonSymbolizer>
"""

_line_template = """
<LineSymbolizer>
  <Stroke>
    <CssParameter name="stroke">%(bg)s</CssParameter>
    <CssParameter name="stroke-width">3</CssParameter>
  </Stroke>
</LineSymbolizer>
</Rule>
</FeatureTypeStyle>
<FeatureTypeStyle>
<Rule>
<LineSymbolizer>
  <Stroke>
    <CssParameter name="stroke">%(fg)s</CssParameter>
  </Stroke>
</LineSymbolizer>
"""

_point_template = """
<PointSymbolizer>
  <Graphic>
    <Mark>
      <WellKnownName>%(mark)s</WellKnownName>
      <Fill>
        <CssParameter name="fill">%(bg)s</CssParameter>
      </Fill>
      <Stroke>
        <CssParameter name="stroke">%(fg)s</CssParameter>
      </Stroke>
    </Mark>
    <Size>10</Size>
  </Graphic>
</PointSymbolizer>
"""

_style_templates = dict(
    raster=_add_sld_boilerplate(_raster_template),
    polygon=_add_sld_boilerplate(_polygon_template),
    line=_add_sld_boilerplate(_line_template),
    point=_add_sld_boilerplate(_point_template)
)


def _style_name(resource):
    return _punc.sub("_", resource.store.workspace.name + ":" + resource.name)


def extract_name_from_sld(gs_catalog, sld, sld_file=None):
    try:
        if sld:
            if isfile(sld):
                sld = open(sld, "r").read()
            dom = etree.XML(sld)
        elif sld_file and isfile(sld_file):
            sld = open(sld_file, "r").read()
            dom = etree.parse(sld_file)
    except Exception:
        logger.exception("The uploaded SLD file is not valid XML")
        raise Exception(
            "The uploaded SLD file is not valid XML")

    named_layer = dom.findall(
        "{http://www.opengis.net/sld}NamedLayer")
    user_layer = dom.findall(
        "{http://www.opengis.net/sld}UserLayer")

    el = None
    if named_layer and len(named_layer) > 0:
        user_style = named_layer[0].findall("{http://www.opengis.net/sld}UserStyle")
        if user_style and len(user_style) > 0:
            el = user_style[0].findall("{http://www.opengis.net/sld}Name")
            if len(el) == 0:
                el = user_style[0].findall("{http://www.opengis.net/se}Name")

        if len(el) == 0:
            el = named_layer[0].findall("{http://www.opengis.net/sld}Name")
        if len(el) == 0:
            el = named_layer[0].findall("{http://www.opengis.net/se}Name")

    if not el or len(el) == 0:
        if user_layer and len(user_layer) > 0:
            user_style = user_layer[0].findall("{http://www.opengis.net/sld}UserStyle")
            if user_style and len(user_style) > 0:
                el = user_style[0].findall("{http://www.opengis.net/sld}Name")
                if len(el) == 0:
                    el = user_style[0].findall("{http://www.opengis.net/se}Name")

            if len(el) == 0:
                el = user_layer[0].findall("{http://www.opengis.net/sld}Name")
            if len(el) == 0:
                el = user_layer[0].findall("{http://www.opengis.net/se}Name")

    if not el or len(el) == 0:
        if sld_file:
            return splitext(basename(sld_file))[0]
        else:
            raise Exception(
                "Please provide a name, unable to extract one from the SLD.")

    return el[0].text


def get_sld_for(gs_catalog, layer):
    # GeoServer sometimes fails to associate a style with the data, so
    # for now we default to using a point style.(it works for lines and
    # polygons, hope this doesn't happen for rasters  though)
    gs_layer = None
    _default_style = None
    try:
        _default_style = layer.default_style
    except BaseException:
        traceback.print_exc()
        pass

    if _default_style is None:
        gs_catalog._cache.clear()
        try:
            gs_layer = gs_catalog.get_layer(layer.name)
            name = gs_layer.default_style.name if gs_layer.default_style is not None else "raster"
        except BaseException:
            traceback.print_exc()
            name = None
    else:
        name = _default_style.name

    # Detect geometry type if it is a FeatureType
    if gs_layer and gs_layer.resource and gs_layer.resource.resource_type == 'featureType':
        res = gs_layer.resource
        res.fetch()
        ft = res.store.get_resources(res.name)
        ft.fetch()
        for attr in ft.dom.find("attributes").getchildren():
            attr_binding = attr.find("binding")
            if "jts.geom" in attr_binding.text:
                if "Polygon" in attr_binding.text:
                    name = "polygon"
                elif "Line" in attr_binding.text:
                    name = "line"
                else:
                    name = "point"

    # FIXME: When gsconfig.py exposes the default geometry type for vector
    # layers we should use that rather than guessing based on the auto-detected
    # style.
    if name in _style_templates:
        fg, bg, mark = _style_contexts.next()
        return _style_templates[name] % dict(
            name=layer.name,
            fg=fg,
            bg=bg,
            mark=mark)
    else:
        return None


def fixup_style(cat, resource, style):
    logger.debug("Creating styles for layers associated with [%s]", resource)
    layers = cat.get_layers(resource=resource)
    logger.info("Found %d layers associated with [%s]", len(layers), resource)
    for lyr in layers:
        if lyr.default_style.name in _style_templates:
            logger.info("%s uses a default style, generating a new one", lyr)
            name = _style_name(lyr)
            if style is None:
                sld = get_sld_for(cat, lyr)
            else:
                sld = style.read()
            logger.info("Creating style [%s]", name)
            style = cat.create_style(name, sld, overwrite=True, raw=True, workspace=settings.DEFAULT_WORKSPACE)
            style = cat.get_style(name, workspace=settings.DEFAULT_WORKSPACE) or cat.get_style(name)
            lyr.default_style = style
            logger.info("Saving changes to %s", lyr)
            cat.save(lyr)
            logger.info("Successfully updated %s", lyr)


def set_layer_style(saved_layer, title, sld, base_file=None):
    # Check SLD is valid
    try:
        if sld:
            if isfile(sld):
                sld = open(sld, "r").read()
            etree.XML(sld)
        elif base_file and isfile(base_file):
            sld = open(base_file, "r").read()
            etree.parse(base_file)
    except Exception:
        logger.exception("The uploaded SLD file is not valid XML")
        raise Exception(
            "The uploaded SLD file is not valid XML")

    # Check Layer's available styles
    match = None
    styles = list(saved_layer.styles.all()) + [
        saved_layer.default_style]
    for style in styles:
        if style and style.name == saved_layer.name:
            match = style
            break
    cat = gs_catalog
    layer = cat.get_layer(title)
    if match is None:
        try:
            cat.create_style(saved_layer.name, sld, raw=True, workspace=settings.DEFAULT_WORKSPACE)
            style = cat.get_style(saved_layer.name, workspace=settings.DEFAULT_WORKSPACE) or \
                cat.get_style(saved_layer.name)
            if layer and style:
                layer.default_style = style
                cat.save(layer)
                saved_layer.default_style = save_style(style)
                set_geowebcache_invalidate_cache(saved_layer.alternate)
        except Exception as e:
            logger.exception(e)
    else:
        style = cat.get_style(saved_layer.name, workspace=settings.DEFAULT_WORKSPACE) or \
            cat.get_style(saved_layer.name)
        # style.update_body(sld)
        try:
            cat.create_style(saved_layer.name, sld, overwrite=True, raw=True,
                             workspace=settings.DEFAULT_WORKSPACE)
            style = cat.get_style(saved_layer.name, workspace=settings.DEFAULT_WORKSPACE) or \
                cat.get_style(saved_layer.name)
            if layer and style:
                layer.default_style = style
                cat.save(layer)
                saved_layer.default_style = save_style(style)
                set_geowebcache_invalidate_cache(saved_layer.alternate)
        except Exception as e:
            logger.exception(e)


def cascading_delete(cat, layer_name):
    resource = None
    try:
        if layer_name.find(':') != -1 and len(layer_name.split(':')) == 2:
            workspace, name = layer_name.split(':')
            ws = cat.get_workspace(workspace)
            try:
                store = get_store(cat, name, workspace=ws)
            except FailedRequestError:
                if ogc_server_settings.DATASTORE:
                    try:
                        layers = Layer.objects.filter(alternate=layer_name)
                        for layer in layers:
                            store = get_store(cat, layer.store, workspace=ws)
                    except FailedRequestError:
                        logger.debug(
                            'the store was not found in geoserver')
                        return
                else:
                    logger.debug(
                        'the store was not found in geoserver')
                    return
            if ws is None:
                logger.debug(
                    'cascading delete was called on a layer where the workspace was not found')
                return
            resource = cat.get_resource(name, store=store, workspace=workspace)
        else:
            resource = cat.get_resource(layer_name)
    except EnvironmentError as e:
        if e.errno == errno.ECONNREFUSED:
            msg = ('Could not connect to geoserver at "%s"'
                   'to save information for layer "%s"' % (
                       ogc_server_settings.LOCATION, layer_name)
                   )
            logger.debug(msg)
            return None
        else:
            raise e

    if resource is None:
        # If there is no associated resource,
        # this method can not delete anything.
        # Let's return and make a note in the log.
        logger.debug(
            'cascading_delete was called with a non existent resource')
        return
    resource_name = resource.name
    lyr = cat.get_layer(resource_name)
    if(lyr is not None):  # Already deleted
        store = resource.store
        styles = lyr.styles
        try:
            styles = styles + [lyr.default_style]
        except BaseException:
            pass
        gs_styles = [x for x in cat.get_styles()]
        if settings.DEFAULT_WORKSPACE:
            gs_styles = gs_styles + [x for x in cat.get_styles(workspace=settings.DEFAULT_WORKSPACE)]
            ws_styles = []
            for s in styles:
                if s is not None and s.name not in _default_style_names:
                    m = re.search(r'\d+$', s.name)
                    _name = s.name[:-len(m.group())] if m else s.name
                    _s = "%s_%s" % (settings.DEFAULT_WORKSPACE, _name)
                    for _gs in gs_styles:
                        if ((_gs.name and _gs.name.startswith("%s_" % settings.DEFAULT_WORKSPACE)) or
                            (_s in _gs.name)) and\
                        _gs not in styles:
                            ws_styles.append(_gs)
            styles = styles + ws_styles
        cat.delete(lyr)
        for s in styles:
            if s is not None and s.name not in _default_style_names:
                try:
                    logger.info("Trying to delete Style [%s]" % s.name)
                    cat.delete(s, purge='true')
                    workspace, name = layer_name.split(':') if ':' in layer_name else \
                        (settings.DEFAULT_WORKSPACE, layer_name)
                except FailedRequestError as e:
                    # Trying to delete a shared style will fail
                    # We'll catch the exception and log it.
                    logger.debug(e)

        # Due to a possible bug of geoserver, we need this trick for now
        # TODO: inspect the issue reported by this hack. Should be solved
        #       with GS 2.7+
        try:
            cat.delete(resource, recurse=True)  # This may fail
        except BaseException:
            cat._cache.clear()
            cat.reset()

        if store.resource_type == 'dataStore' and 'dbtype' in store.connection_parameters and \
                store.connection_parameters['dbtype'] == 'postgis':
            delete_from_postgis(resource_name, store)
        else:
            if store.resource_type == 'coverageStore':
                try:
                    logger.info(" - Going to purge the " + store.resource_type + " : " + store.href)
                    cat.reset()  # this resets the coverage readers and unlocks the files
                    cat.delete(store, purge='all', recurse=True)
                    # cat.reload()  # this preservers the integrity of geoserver
                except FailedRequestError as e:
                    # Trying to recursively purge a store may fail
                    # We'll catch the exception and log it.
                    logger.debug(e)
            else:
                try:
                    if not store.get_resources():
                        cat.delete(store, recurse=True)
                except FailedRequestError as e:
                    # Catch the exception and log it.
                    logger.debug(e)


def delete_from_postgis(layer_name, store):
    """
    Delete a table from PostGIS (because Geoserver won't do it yet);
    to be used after deleting a layer from the system.
    """
    import psycopg2

    # we will assume that store/database may change (when using shard for example)
    # but user and password are the ones from settings (DATASTORE_URL)
    db = ogc_server_settings.datastore_db
    db_name = store.connection_parameters['database']
    user = db['USER']
    password = db['PASSWORD']
    host = store.connection_parameters['host']
    port = store.connection_parameters['port']
    conn = None
    try:
        conn = psycopg2.connect(dbname=db_name, user=user, host=host, port=port, password=password)
        cur = conn.cursor()
        cur.execute("SELECT DropGeometryTable ('%s')" % layer_name)
        conn.commit()
    except Exception as e:
        logger.error(
            "Error deleting PostGIS table %s:%s",
            layer_name,
            str(e))
    finally:
        try:
            if conn:
                conn.close()
        except Exception as e:
            logger.error("Error closing PostGIS conn %s:%s", layer_name, str(e))


def gs_slurp(
        ignore_errors=True,
        verbosity=1,
        console=None,
        owner=None,
        workspace=None,
        store=None,
        filter=None,
        skip_unadvertised=False,
        skip_geonode_registered=False,
        remove_deleted=False,
        permissions=None,
        execute_signals=False):
    """Configure the layers available in GeoServer in GeoNode.

       It returns a list of dictionaries with the name of the layer,
       the result of the operation and the errors and traceback if it failed.
    """
    if console is None:
        console = open(os.devnull, 'w')

    if verbosity > 0:
        print >> console, "Inspecting the available layers in GeoServer ..."
    cat = Catalog(ogc_server_settings.internal_rest, _user, _password)
    if workspace is not None:
        workspace = cat.get_workspace(workspace)
        if workspace is None:
            resources = []
        else:
            # obtain the store from within the workspace. if it exists, obtain resources
            # directly from store, otherwise return an empty list:
            if store is not None:
                store = get_store(cat, store, workspace=workspace)
                if store is None:
                    resources = []
                else:
                    resources = cat.get_resources(store=store)
            else:
                resources = cat.get_resources(workspace=workspace)

    elif store is not None:
        store = get_store(cat, store)
        resources = cat.get_resources(store=store)
    else:
        resources = cat.get_resources()
    if remove_deleted:
        resources_for_delete_compare = resources[:]
        workspace_for_delete_compare = workspace
        # filter out layers for delete comparison with GeoNode layers by following criteria:
        # enabled = true, if --skip-unadvertised: advertised = true, but
        # disregard the filter parameter in the case of deleting layers
        resources_for_delete_compare = [
            k for k in resources_for_delete_compare if k.enabled in ["true", True]]
        if skip_unadvertised:
            resources_for_delete_compare = [
                k for k in resources_for_delete_compare if k.advertised in ["true", True]]

    if filter:
        resources = [k for k in resources if filter in k.name]

    # filter out layers depending on enabled, advertised status:
    resources = [k for k in resources if k.enabled in ["true", True]]
    if skip_unadvertised:
        resources = [k for k in resources if k.advertised in ["true", True]]

    # filter out layers already registered in geonode
    layer_names = Layer.objects.all().values_list('alternate', flat=True)
    if skip_geonode_registered:
        resources = [k for k in resources
                     if not '%s:%s' % (k.workspace.name, k.name) in layer_names]

    # TODO: Should we do something with these?
    # i.e. look for matching layers in GeoNode and also disable?
    # disabled_resources = [k for k in resources if k.enabled == "false"]

    number = len(resources)
    if verbosity > 0:
        msg = "Found %d layers, starting processing" % number
        print >> console, msg
    output = {
        'stats': {
            'failed': 0,
            'updated': 0,
            'created': 0,
            'deleted': 0,
        },
        'layers': [],
        'deleted_layers': []
    }
    start = datetime.datetime.now(timezone.get_current_timezone())
    for i, resource in enumerate(resources):
        name = resource.name
        the_store = resource.store
        workspace = the_store.workspace
        try:
            layer, created = Layer.objects.get_or_create(name=name, workspace=workspace.name, defaults={
                # "workspace": workspace.name,
                "store": the_store.name,
                "storeType": the_store.resource_type,
                "alternate": "%s:%s" % (workspace.name.encode('utf-8'), resource.name.encode('utf-8')),
                "title": resource.title or 'No title provided',
                "abstract": resource.abstract or unicode(_('No abstract provided')).encode('utf-8'),
                "owner": owner,
                "uuid": str(uuid.uuid4()),
                "bbox_x0": Decimal(resource.native_bbox[0]),
                "bbox_x1": Decimal(resource.native_bbox[1]),
                "bbox_y0": Decimal(resource.native_bbox[2]),
                "bbox_y1": Decimal(resource.native_bbox[3]),
                "srid": resource.projection
            })

            # sync permissions in GeoFence
            perm_spec = json.loads(_perms_info_json(layer))
            layer.set_permissions(perm_spec)

            # recalculate the layer statistics
            set_attributes_from_geoserver(layer, overwrite=True)

            # in some cases we need to explicitily save the resource to execute the signals
            # (for sure when running updatelayers)
            if execute_signals:
                layer.save()

            # Fix metadata links if the ip has changed
            if layer.link_set.metadata().count() > 0:
                if not created and settings.SITEURL not in layer.link_set.metadata()[0].url:
                    layer.link_set.metadata().delete()
                    layer.save()
                    metadata_links = []
                    for link in layer.link_set.metadata():
                        metadata_links.append((link.mime, link.name, link.url))
                    resource.metadata_links = metadata_links
                    cat.save(resource)

        except Exception as e:
            if ignore_errors:
                status = 'failed'
                exception_type, error, traceback = sys.exc_info()
            else:
                if verbosity > 0:
                    msg = "Stopping process because --ignore-errors was not set and an error was found."
                    print >> sys.stderr, msg
                raise Exception(
                    'Failed to process %s' %
                    resource.name.encode('utf-8'), e), None, sys.exc_info()[2]
        else:
            if created:
                if not permissions:
                    layer.set_default_permissions()
                else:
                    layer.set_permissions(permissions)

                status = 'created'
                output['stats']['created'] += 1
            else:
                status = 'updated'
                output['stats']['updated'] += 1

        msg = "[%s] Layer %s (%d/%d)" % (status, name, i + 1, number)
        info = {'name': name, 'status': status}
        if status == 'failed':
            output['stats']['failed'] += 1
            info['traceback'] = traceback
            info['exception_type'] = exception_type
            info['error'] = error
        output['layers'].append(info)
        if verbosity > 0:
            print >> console, msg

    if remove_deleted:
        q = Layer.objects.filter()
        if workspace_for_delete_compare is not None:
            if isinstance(workspace_for_delete_compare, Workspace):
                q = q.filter(
                    workspace__exact=workspace_for_delete_compare.name)
            else:
                q = q.filter(workspace__exact=workspace_for_delete_compare)
        if store is not None:
            if isinstance(
                    store,
                    CoverageStore) or isinstance(
                    store,
                    DataStore):
                q = q.filter(store__exact=store.name)
            else:
                q = q.filter(store__exact=store)
        logger.debug("Executing 'remove_deleted' logic")
        logger.debug("GeoNode Layers Found:")

        # compare the list of GeoNode layers obtained via query/filter with valid resources found in GeoServer
        # filtered per options passed to updatelayers: --workspace, --store, --skip-unadvertised
        # add any layers not found in GeoServer to deleted_layers (must match
        # workspace and store as well):
        deleted_layers = []
        for layer in q:
            logger.debug(
                "GeoNode Layer info: name: %s, workspace: %s, store: %s",
                layer.name,
                layer.workspace,
                layer.store)
            layer_found_in_geoserver = False
            for resource in resources_for_delete_compare:
                # if layer.name matches a GeoServer resource, check also that
                # workspace and store match, mark valid:
                if layer.name == resource.name:
                    if layer.workspace == resource.workspace.name and layer.store == resource.store.name:
                        logger.debug(
                            "Matches GeoServer layer: name: %s, workspace: %s, store: %s",
                            resource.name,
                            resource.workspace.name,
                            resource.store.name)
                        layer_found_in_geoserver = True
            if not layer_found_in_geoserver:
                logger.debug(
                    "----- Layer %s not matched, marked for deletion ---------------",
                    layer.name)
                deleted_layers.append(layer)

        number_deleted = len(deleted_layers)
        if verbosity > 0:
            msg = "\nFound %d layers to delete, starting processing" % number_deleted if number_deleted > 0 else \
                "\nFound %d layers to delete" % number_deleted
            print >> console, msg

        for i, layer in enumerate(deleted_layers):
            logger.debug(
                "GeoNode Layer to delete: name: %s, workspace: %s, store: %s",
                layer.name,
                layer.workspace,
                layer.store)
            try:
                # delete ratings, comments, and taggit tags:
                ct = ContentType.objects.get_for_model(layer)
                OverallRating.objects.filter(
                    content_type=ct,
                    object_id=layer.id).delete()
                Comment.objects.filter(
                    content_type=ct,
                    object_id=layer.id).delete()
                layer.keywords.clear()

                layer.delete()
                output['stats']['deleted'] += 1
                status = "delete_succeeded"
            except Exception as e:
                status = "delete_failed"
            finally:
                from .signals import geoserver_pre_delete
                pre_delete.connect(geoserver_pre_delete, sender=Layer)

            msg = "[%s] Layer %s (%d/%d)" % (status,
                                             layer.name,
                                             i + 1,
                                             number_deleted)
            info = {'name': layer.name, 'status': status}
            if status == "delete_failed":
                exception_type, error, traceback = sys.exc_info()
                info['traceback'] = traceback
                info['exception_type'] = exception_type
                info['error'] = error
            output['deleted_layers'].append(info)
            if verbosity > 0:
                print >> console, msg

    finish = datetime.datetime.now(timezone.get_current_timezone())
    td = finish - start
    output['stats']['duration_sec'] = td.microseconds / \
        1000000 + td.seconds + td.days * 24 * 3600
    return output


def get_stores(store_type=None):
    cat = Catalog(ogc_server_settings.internal_rest, _user, _password)
    stores = cat.get_stores()
    store_list = []
    for store in stores:
        store.fetch()
        stype = store.dom.find('type').text.lower()
        if store_type and store_type.lower() == stype:
            store_list.append({'name': store.name, 'type': stype})
        elif store_type is None:
            store_list.append({'name': store.name, 'type': stype})
    return store_list


def set_attributes(
        layer,
        attribute_map,
        overwrite=False,
        attribute_stats=None):
    """ *layer*: a geonode.layers.models.Layer instance
        *attribute_map*: a list of 2-lists specifying attribute names and types,
            example: [ ['id', 'Integer'], ... ]
        *overwrite*: replace existing attributes with new values if name/type matches.
        *attribute_stats*: dictionary of return values from get_attribute_statistics(),
            of the form to get values by referencing attribute_stats[<layer_name>][<field_name>].
    """
    # we need 3 more items; description, attribute_label, and display_order
    attribute_map_dict = {
        'field': 0,
        'ftype': 1,
        'description': 2,
        'label': 3,
        'display_order': 4,
    }
    for attribute in attribute_map:
        attribute.extend((None, None, 0))

    attributes = layer.attribute_set.all()
    # Delete existing attributes if they no longer exist in an updated layer
    for la in attributes:
        lafound = False
        for attribute in attribute_map:
            field, ftype, description, label, display_order = attribute
            if field == la.attribute:
                lafound = True
                # store description and attribute_label in attribute_map
                attribute[attribute_map_dict['description']] = la.description
                attribute[attribute_map_dict['label']] = la.attribute_label
                attribute[attribute_map_dict['display_order']
                          ] = la.display_order
        if overwrite or not lafound:
            logger.debug(
                "Going to delete [%s] for [%s]",
                la.attribute,
                layer.name.encode('utf-8'))
            la.delete()

    # Add new layer attributes if they don't already exist
    if attribute_map is not None:
        iter = len(Attribute.objects.filter(layer=layer)) + 1
        for attribute in attribute_map:
            field, ftype, description, label, display_order = attribute
            if field is not None:
                la, created = Attribute.objects.get_or_create(
                    layer=layer, attribute=field, attribute_type=ftype,
                    description=description, attribute_label=label,
                    display_order=display_order)
                if created:
                    if (not attribute_stats or layer.name not in attribute_stats or
                            field not in attribute_stats[layer.name]):
                        result = None
                    else:
                        result = attribute_stats[layer.name][field]

                    if result is not None:
                        logger.debug("Generating layer attribute statistics")
                        la.count = result['Count']
                        la.min = result['Min']
                        la.max = result['Max']
                        la.average = result['Average']
                        la.median = result['Median']
                        la.stddev = result['StandardDeviation']
                        la.sum = result['Sum']
                        la.unique_values = result['unique_values']
                        la.last_stats_updated = datetime.datetime.now(timezone.get_current_timezone())
                    la.visible = ftype.find("gml:") != 0
                    la.display_order = iter
                    la.save()
                    iter += 1
                    logger.debug(
                        "Created [%s] attribute for [%s]",
                        field,
                        layer.name.encode('utf-8'))
    else:
        logger.debug("No attributes found")


def set_attributes_from_geoserver(layer, overwrite=False):
    """
    Retrieve layer attribute names & types from Geoserver,
    then store in GeoNode database using Attribute model
    """
    attribute_map = []
    server_url = ogc_server_settings.LOCATION if layer.storeType != "remoteStore" else layer.remote_service.service_url

    if layer.storeType == "remoteStore" and layer.remote_service.ptype == "gxp_arcrestsource":
        dft_url = server_url + ("%s?f=json" % layer.alternate)
        try:
            # The code below will fail if http_client cannot be imported
            req, body = http_client.get(dft_url)
            body = json.loads(body)
            attribute_map = [[n["name"], _esri_types[n["type"]]]
                             for n in body["fields"] if n.get("name") and n.get("type")]
        except BaseException:
            tb = traceback.format_exc()
            logger.debug(tb)
            attribute_map = []
    elif layer.storeType in ["dataStore", "remoteStore", "wmsStore"]:
        dft_url = re.sub(r"\/wms\/?$",
                         "/",
                         server_url) + "ows?" + urllib.urlencode({"service": "wfs",
                                                                  "version": "1.0.0",
                                                                  "request": "DescribeFeatureType",
                                                                  "typename": layer.alternate.encode('utf-8'),
                                                                  })
        try:
            # The code below will fail if http_client cannot be imported  or
            # WFS not supported
            req, body = http_client.get(dft_url)
            doc = etree.fromstring(body)
            path = ".//{xsd}extension/{xsd}sequence/{xsd}element".format(
                xsd="{http://www.w3.org/2001/XMLSchema}")
            attribute_map = [[n.attrib["name"], n.attrib["type"]] for n in doc.findall(
                path) if n.attrib.get("name") and n.attrib.get("type")]
        except BaseException:
            tb = traceback.format_exc()
            logger.debug(tb)
            attribute_map = []
            # Try WMS instead
            dft_url = server_url + "?" + urllib.urlencode({
                "service": "wms",
                "version": "1.0.0",
                "request": "GetFeatureInfo",
                "bbox": ','.join([str(x) for x in layer.bbox]),
                "LAYERS": layer.alternate.encode('utf-8'),
                "QUERY_LAYERS": layer.alternate.encode('utf-8'),
                "feature_count": 1,
                "width": 1,
                "height": 1,
                "srs": "EPSG:4326",
                "info_format": "text/html",
                "x": 1,
                "y": 1
            })
            try:
                req, body = http_client.get(dft_url)
                soup = BeautifulSoup(body)
                for field in soup.findAll('th'):
                    if(field.string is None):
                        field_name = field.contents[0].string
                    else:
                        field_name = field.string
                    attribute_map.append([field_name, "xsd:string"])
            except BaseException:
                tb = traceback.format_exc()
                logger.debug(tb)
                attribute_map = []

    elif layer.storeType in ["coverageStore"]:
        dc_url = server_url + "wcs?" + urllib.urlencode({
            "service": "wcs",
            "version": "1.1.0",
            "request": "DescribeCoverage",
            "identifiers": layer.alternate.encode('utf-8')
        })
        try:
            req, body = http_client.get(dc_url)
            doc = etree.fromstring(body)
            path = ".//{wcs}Axis/{wcs}AvailableKeys/{wcs}Key".format(
                wcs="{http://www.opengis.net/wcs/1.1.1}")
            attribute_map = [[n.text, "raster"] for n in doc.findall(path)]
        except BaseException:
            tb = traceback.format_exc()
            logger.debug(tb)
            attribute_map = []

    # Get attribute statistics & package for call to really_set_attributes()
    attribute_stats = defaultdict(dict)
    # Add new layer attributes if they don't already exist
    for attribute in attribute_map:
        field, ftype = attribute
        if field is not None:
            if Attribute.objects.filter(layer=layer, attribute=field).exists():
                continue
            else:
                if is_layer_attribute_aggregable(
                        layer.storeType,
                        field,
                        ftype):
                    logger.debug("Generating layer attribute statistics")
                    result = get_attribute_statistics(layer.alternate, field)
                else:
                    result = None
                attribute_stats[layer.name][field] = result

    set_attributes(
        layer, attribute_map, overwrite=overwrite, attribute_stats=attribute_stats
    )


def set_styles(layer, gs_catalog):
    style_set = []

    gs_layer = gs_catalog.get_layer(layer.name)
    if not gs_layer:
        gs_layer = gs_catalog.get_layer(layer.alternate)

    if gs_layer:
        default_style = None
        try:
            default_style = gs_layer.default_style or None
        except BaseException:
            tb = traceback.format_exc()
            logger.debug(tb)
            pass

        if not default_style:
            try:
                default_style = gs_catalog.get_style(layer.name, workspace=layer.workspace) \
                    or gs_catalog.get_style(layer.name)
                gs_layer.default_style = default_style
                gs_catalog.save(gs_layer)
            except BaseException:
                tb = traceback.format_exc()
                logger.debug(tb)
                logger.exception("GeoServer Layer Default Style issues!")

        if default_style:
            # make sure we are not using a defaul SLD (which won't be editable)
            if not default_style.workspace or default_style.workspace != layer.workspace:
                sld_body = default_style.sld_body
                try:
                    gs_catalog.create_style(layer.name, sld_body, raw=True, workspace=layer.workspace)
                except BaseException:
                    tb = traceback.format_exc()
                    logger.debug(tb)
                    pass
                style = gs_catalog.get_style(layer.name, workspace=layer.workspace)
            else:
                style = default_style
            if style:
                layer.default_style = save_style(style)
                style_set.append(layer.default_style)
        try:
            if gs_layer.styles:
                alt_styles = gs_layer.styles
                for alt_style in alt_styles:
                    if alt_style:
                        style_set.append(save_style(alt_style))
        except BaseException:
            tb = traceback.format_exc()
            logger.debug(tb)
            pass

    layer.styles = style_set

    # Update default style to database
    to_update = {
        'default_style': layer.default_style
    }

    Layer.objects.filter(id=layer.id).update(**to_update)
    layer.refresh_from_db()


def save_style(gs_style):
    style, created = Style.objects.get_or_create(name=gs_style.name)
    try:
        style.sld_title = gs_style.sld_title
    except BaseException:
        tb = traceback.format_exc()
        logger.debug(tb)
        style.sld_title = gs_style.name
    finally:
        style.sld_body = gs_style.sld_body
        style.sld_url = gs_style.body_href
        style.save()
    return style


def is_layer_attribute_aggregable(store_type, field_name, field_type):
    """
    Decipher whether layer attribute is suitable for statistical derivation
    """

    # must be vector layer
    if store_type != 'dataStore':
        return False
    # must be a numeric data type
    if field_type not in LAYER_ATTRIBUTE_NUMERIC_DATA_TYPES:
        return False
    # must not be an identifier type field
    if field_name.lower() in ['id', 'identifier']:
        return False

    return True


def get_attribute_statistics(layer_name, field):
    """
    Generate statistics (range, mean, median, standard deviation, unique values)
    for layer attribute
    """

    logger.debug('Deriving aggregate statistics for attribute %s', field)

    if not ogc_server_settings.WPS_ENABLED:
        return None
    try:
        return wps_execute_layer_attribute_statistics(layer_name, field)
    except BaseException:
        tb = traceback.format_exc()
        logger.debug(tb)
        logger.exception('Error generating layer aggregate statistics')


def get_wcs_record(instance, retry=True):
    wcs = WebCoverageService(ogc_server_settings.LOCATION + 'wcs', '1.0.0')
    key = instance.workspace + ':' + instance.name
    logger.debug(wcs.contents)
    if key in wcs.contents:
        return wcs.contents[key]
    else:
        msg = ("Layer '%s' was not found in WCS service at %s." %
               (key, ogc_server_settings.public_url)
               )
        if retry:
            logger.debug(
                msg +
                ' Waiting a couple of seconds before trying again.')
            time.sleep(2)
            return get_wcs_record(instance, retry=False)
        else:
            raise GeoNodeException(msg)


def get_coverage_grid_extent(instance):
    """
        Returns a list of integers with the size of the coverage
        extent in pixels
    """
    instance_wcs = get_wcs_record(instance)
    grid = instance_wcs.grid
    return [(int(h) - int(l) + 1) for
            h, l in zip(grid.highlimits, grid.lowlimits)]


GEOSERVER_LAYER_TYPES = {
    'vector': FeatureType.resource_type,
    'raster': Coverage.resource_type,
}


def cleanup(name, uuid):
    """Deletes GeoServer and Catalogue records for a given name.

       Useful to clean the mess when something goes terribly wrong.
       It also verifies if the Django record existed, in which case
       it performs no action.
    """
    try:
        Layer.objects.get(name=name)
    except Layer.DoesNotExist as e:
        pass
    else:
        msg = ('Not doing any cleanup because the layer %s exists in the '
               'Django db.' % name)
        raise GeoNodeException(msg)

    cat = gs_catalog
    gs_store = None
    gs_layer = None
    gs_resource = None
    # FIXME: Could this lead to someone deleting for example a postgis db
    # with the same name of the uploaded file?.
    try:
        gs_store = cat.get_store(name)
        if gs_store is not None:
            gs_layer = cat.get_layer(name)
            if gs_layer is not None:
                gs_resource = gs_layer.resource
        else:
            gs_layer = None
            gs_resource = None
    except FailedRequestError as e:
        msg = ('Couldn\'t connect to GeoServer while cleaning up layer '
               '[%s] !!', str(e))
        logger.warning(msg)

    if gs_layer is not None:
        try:
            cat.delete(gs_layer)
        except BaseException:
            logger.warning("Couldn't delete GeoServer layer during cleanup()")
    if gs_resource is not None:
        try:
            cat.delete(gs_resource)
        except BaseException:
            msg = 'Couldn\'t delete GeoServer resource during cleanup()'
            logger.warning(msg)
    if gs_store is not None:
        try:
            cat.delete(gs_store)
        except BaseException:
            logger.warning("Couldn't delete GeoServer store during cleanup()")

    logger.warning('Deleting dangling Catalogue record for [%s] '
                   '(no Django record to match)', name)

    if 'geonode.catalogue' in settings.INSTALLED_APPS:
        from geonode.catalogue import get_catalogue
        catalogue = get_catalogue()
        catalogue.remove_record(uuid)
        logger.warning('Finished cleanup after failed Catalogue/Django '
                       'import for layer: %s', name)


def create_geoserver_db_featurestore(
        store_type=None, store_name=None,
        author_name='admin', author_email='admin@geonode.org',
        charset="UTF-8", workspace=None):
    cat = gs_catalog
    dsname = store_name or ogc_server_settings.DATASTORE
    # get or create datastore
    ds_exists = False
    try:
        if dsname:
            ds = cat.get_store(dsname)
        else:
            return None
        if ds is None:
            raise FailedRequestError
        ds_exists = True
    except FailedRequestError:
        logging.info(
            'Creating target datastore %s' % dsname)
        ds = cat.create_datastore(dsname, workspace=workspace)
        db = ogc_server_settings.datastore_db
        db_engine = 'postgis' if \
            'postgis' in db['ENGINE'] else db['ENGINE']
        ds.connection_parameters.update(
            {'Evictor run periodicity': 300,
             'Estimated extends': 'true',
             'Estimated extends': 'true',
             'fetch size': 100000,
             'encode functions': 'false',
             'Expose primary keys': 'true',
             'validate connections': 'true',
             'Support on the fly geometry simplification': 'true',
             'Connection timeout': 300,
             'create database': 'false',
             'Batch insert size': 30,
             'preparedStatements': 'true',
             'min connections': 10,
             'max connections': 100,
             'Evictor tests per run': 3,
             'Max connection idle time': 300,
             'Loose bbox': 'true',
             'Test while idle': 'true',
             'host': db['HOST'],
             'port': db['PORT'] if isinstance(
                 db['PORT'], basestring) else str(db['PORT']) or '5432',
             'database': db['NAME'],
             'user': db['USER'],
             'passwd': db['PASSWORD'],
             'dbtype': db_engine}
        )

    if ds_exists:
        ds.save_method = "PUT"

    cat.save(ds)
    ds = get_store(cat, dsname, workspace=workspace)
    assert ds.enabled

    return ds


def _create_featurestore(name, data, overwrite=False, charset="UTF-8", workspace=None):

    cat = gs_catalog
    try:
        cat.create_featurestore(name, data, overwrite=overwrite, charset=charset)
    except BaseException as e:
        logger.exception(e)
    store = get_store(cat, name, workspace=workspace)
    return store, cat.get_resource(name, store=store, workspace=workspace)


def _create_coveragestore(name, data, overwrite=False, charset="UTF-8", workspace=None):
    cat = gs_catalog
    try:
        cat.create_coveragestore(name, data, overwrite=overwrite)
    except BaseException as e:
        logger.exception(e)
    store = get_store(cat, name, workspace=workspace)
    return store, cat.get_resource(name, store=store, workspace=workspace)


def _create_db_featurestore(name, data, overwrite=False, charset="UTF-8", workspace=None):
    """Create a database store then use it to import a shapefile.

    If the import into the database fails then delete the store
    (and delete the PostGIS table for it).
    """
    cat = gs_catalog
    db = ogc_server_settings.datastore_db
    # dsname = ogc_server_settings.DATASTORE
    dsname = db['NAME']
    ds = create_geoserver_db_featurestore(store_name=dsname, workspace=workspace)

    try:
        cat.add_data_to_store(ds,
                              name,
                              data,
                              overwrite=overwrite,
                              workspace=workspace,
                              charset=charset)
        resource = cat.get_resource(name, store=ds, workspace=workspace)
        assert resource is not None
        return ds, resource
    except Exception:
        msg = _("An exception occurred loading data to PostGIS")
        msg += "- %s" % (sys.exc_info()[1])
        try:
            delete_from_postgis(name, ds)
        except Exception:
            msg += _(" Additionally an error occured during database cleanup")
            msg += "- %s" % (sys.exc_info()[1])
        raise GeoNodeException(msg)


def get_store(cat, name, workspace=None):

    # Make sure workspace is a workspace object and not a string.
    # If the workspace does not exist, continue as if no workspace had been defined.
    if isinstance(workspace, basestring):
        workspace = cat.get_workspace(workspace)

    if workspace is None:
        workspace = cat.get_default_workspace()

    if workspace:
        try:
            store = cat.get_xml('%s/%s.xml' % (workspace.datastore_url[:-4], name))
        except FailedRequestError:
            try:
                store = cat.get_xml('%s/%s.xml' % (workspace.coveragestore_url[:-4], name))
            except FailedRequestError:
                try:
                    store = cat.get_xml('%s/%s.xml' % (workspace.wmsstore_url[:-4], name))
                except FailedRequestError:
                    raise FailedRequestError("No store found named: " + name)
        if store:
            if store.tag == 'dataStore':
                store = datastore_from_index(cat, workspace, store)
            elif store.tag == 'coverageStore':
                store = coveragestore_from_index(cat, workspace, store)
            elif store.tag == 'wmsStore':
                store = wmsstore_from_index(cat, workspace, store)

            return store
        else:
            raise FailedRequestError("No store found named: " + name)
    else:
        raise FailedRequestError("No store found named: " + name)


class ServerDoesNotExist(Exception):
    pass


class OGC_Server(object):

    """
    OGC Server object.
    """

    def __init__(self, ogc_server, alias):
        self.alias = alias
        self.server = ogc_server

    def __getattr__(self, item):
        return self.server.get(item)

    @property
    def credentials(self):
        """
        Returns a tuple of the server's credentials.
        """
        creds = namedtuple('OGC_SERVER_CREDENTIALS', ['username', 'password'])
        return creds(username=self.USER, password=self.PASSWORD)

    @property
    def datastore_db(self):
        """
        Returns the server's datastore dict or None.
        """
        if self.DATASTORE and settings.DATABASES.get(self.DATASTORE, None):
            datastore_dict = settings.DATABASES.get(self.DATASTORE, dict())
            if hasattr(settings, 'SHARD_STRATEGY'):
                if settings.SHARD_STRATEGY:
                    from geonode.contrib.datastore_shards.utils import get_shard_database_name
                    datastore_dict['NAME'] = get_shard_database_name()
            return datastore_dict
        else:
            return dict()

    @property
    def ows(self):
        """
        The Open Web Service url for the server.
        """
        location = self.PUBLIC_LOCATION if self.PUBLIC_LOCATION else self.LOCATION
        return self.OWS_LOCATION if self.OWS_LOCATION else urljoin(location, 'ows')

    @property
    def rest(self):
        """
        The REST endpoint for the server.
        """
        return urljoin(self.LOCATION, 'rest') if not self.REST_LOCATION else self.REST_LOCATION

    @property
    def public_url(self):
        """
        The global public endpoint for the server.
        """
        return self.LOCATION if not self.PUBLIC_LOCATION else self.PUBLIC_LOCATION

    @property
    def internal_ows(self):
        """
        The Open Web Service url for the server used by GeoNode internally.
        """
        location = self.LOCATION
        return urljoin(location, 'ows')

    @property
    def internal_rest(self):
        """
        The internal REST endpoint for the server.
        """
        return urljoin(self.LOCATION, 'rest')

    @property
    def hostname(self):
        return urlsplit(self.LOCATION).hostname

    @property
    def netloc(self):
        return urlsplit(self.LOCATION).netloc

    def __str__(self):
        return self.alias


class OGC_Servers_Handler(object):

    """
    OGC Server Settings Convenience dict.
    """

    def __init__(self, ogc_server_dict):
        self.servers = ogc_server_dict
        # FIXME(Ariel): Are there better ways to do this without involving
        # local?
        self._servers = local()

    def ensure_valid_configuration(self, alias):
        """
        Ensures the settings are valid.
        """
        try:
            server = self.servers[alias]
        except KeyError:
            raise ServerDoesNotExist("The server %s doesn't exist" % alias)

        datastore = server.get('DATASTORE')
        uploader_backend = getattr(
            settings,
            'UPLOADER',
            dict()).get(
            'BACKEND',
            'geonode.rest')

        if uploader_backend == 'geonode.importer' and datastore and not settings.DATABASES.get(
                datastore):
            raise ImproperlyConfigured(
                'The OGC_SERVER setting specifies a datastore '
                'but no connection parameters are present.')

        if uploader_backend == 'geonode.importer' and not datastore:
            raise ImproperlyConfigured(
                'The UPLOADER BACKEND is set to geonode.importer but no DATASTORE is specified.')

        if 'PRINTNG_ENABLED' in server:
            raise ImproperlyConfigured("The PRINTNG_ENABLED setting has been removed, use 'PRINT_NG_ENABLED' instead.")

    def ensure_defaults(self, alias):
        """
        Puts the defaults into the settings dictionary for a given connection where no settings is provided.
        """
        try:
            server = self.servers[alias]
        except KeyError:
            raise ServerDoesNotExist("The server %s doesn't exist" % alias)

        server.setdefault('BACKEND', 'geonode.geoserver')
        server.setdefault('LOCATION', 'http://localhost:8080/geoserver/')
        server.setdefault('USER', 'admin')
        server.setdefault('PASSWORD', 'geoserver')
        server.setdefault('DATASTORE', str())

        for option in ['MAPFISH_PRINT_ENABLED', 'PRINT_NG_ENABLED', 'GEONODE_SECURITY_ENABLED',
                       'GEOFENCE_SECURITY_ENABLED', 'BACKEND_WRITE_ENABLED']:
            server.setdefault(option, True)

        for option in ['WMST_ENABLED', 'WPS_ENABLED']:
            server.setdefault(option, False)

    def __getitem__(self, alias):
        if hasattr(self._servers, alias):
            return getattr(self._servers, alias)

        self.ensure_defaults(alias)
        self.ensure_valid_configuration(alias)
        server = self.servers[alias]
        server = OGC_Server(alias=alias, ogc_server=server)
        setattr(self._servers, alias, server)
        return server

    def __setitem__(self, key, value):
        setattr(self._servers, key, value)

    def __iter__(self):
        return iter(self.servers)

    def all(self):
        return [self[alias] for alias in self]


def get_wms():
    wms_url = ogc_server_settings.internal_ows + \
        "?service=WMS&request=GetCapabilities&version=1.1.0"
    req, body = http_client.get(wms_url)
    _wms = WebMapService(wms_url, xml=body)
    return _wms


def wps_execute_layer_attribute_statistics(layer_name, field):
    """Derive aggregate statistics from WPS endpoint"""

    # generate statistics using WPS
    url = urljoin(ogc_server_settings.LOCATION, 'ows')

    request = render_to_string('layers/wps_execute_gs_aggregate.xml', {
                               'layer_name': layer_name,
                               'field': field
                               })
    u = urlsplit(url)

    headers = {
        'User-Agent': 'OWSLib (https://geopython.github.io/OWSLib)',
        'Content-type': 'text/xml',
        'Accept': 'text/xml',
        'Accept-Language': 'en-US',
        'Accept-Encoding': 'gzip,deflate',
        'Host': u.netloc,
    }

    response, content = http_client.request(
        url,
        method='POST',
        data=request,
        headers=headers)

    exml = etree.fromstring(content)

    result = {}

    for f in ['Min', 'Max', 'Average', 'Median', 'StandardDeviation', 'Sum']:
        fr = exml.find(f)
        if fr is not None:
            result[f] = fr.text
        else:
            result[f] = 'NA'

    count = exml.find('Count')
    if count is not None:
        result['Count'] = int(count.text)
    else:
        result['Count'] = 0

    result['unique_values'] = 'NA'

    return result


def _stylefilterparams_geowebcache_layer(layer_name):
    headers = {
        "Content-Type": "text/xml"
    }
    url = '%sgwc/rest/layers/%s.xml' % (ogc_server_settings.LOCATION, layer_name)

    # read GWC configuration
    req, content = http_client.get(url, headers=headers)
    if req.status_code != 200:
        line = "Error {0} reading Style Filter Params GeoWebCache at {1}".format(
            req.status_code, url
        )
        logger.error(line)
        return

    # check/write GWC filter parameters
    import xml.etree.ElementTree as ET
    body = None
    tree = ET.fromstring(_)
    param_filters = tree.findall('parameterFilters')
    if param_filters and len(param_filters) > 0:
        if not param_filters[0].findall('styleParameterFilter'):
            style_filters_xml = "<styleParameterFilter><key>STYLES</key>\
                <defaultValue></defaultValue></styleParameterFilter>"
            style_filters_elem = ET.fromstring(style_filters_xml)
            param_filters[0].append(style_filters_elem)
            body = ET.tostring(tree)
    if body:
        req, content = http_client.post(url, data=body, headers=headers)
        if req.status_code != 200:
            line = "Error {0} writing Style Filter Params GeoWebCache at {1}".format(
                req.status_code, url
            )
            logger.error(line)


def _invalidate_geowebcache_layer(layer_name, url=None):
    # http.add_credentials(username, password)
    headers = {
        "Content-Type": "text/xml",
    }
    body = """
        <truncateLayer><layerName>{0}</layerName></truncateLayer>
        """.strip().format(layer_name)
    if not url:
        url = '%sgwc/rest/masstruncate' % ogc_server_settings.LOCATION
    req, content = http_client.post(url, data=body, headers=headers)

    if req.status_code != 200:
        line = "Error {0} invalidating GeoWebCache at {1}".format(
            req.status_code, url
        )
        logger.error(line)


def style_update(request, url):
    """
    Sync style stuff from GS to GN.
    Ideally we should call this from a view straight from GXP, and we should use
    gsConfig, that at this time does not support styles updates. Before gsConfig
    is updated, for now we need to parse xml.
    In case of a DELETE, we need to query request.path to get the style name,
    and then remove it.
    In case of a POST or PUT, we need to parse the xml from
    request.body, which is in this format:
    """
    affected_layers = []
    if request.method in ('POST', 'PUT', 'DELETE'):  # we need to parse xml
        # Need to remove NSx from IE11
        if "HTTP_USER_AGENT" in request.META:
            if ('Trident/7.0' in request.META['HTTP_USER_AGENT'] and
                    'rv:11.0' in request.META['HTTP_USER_AGENT']):
                txml = re.sub(r'xmlns:NS[0-9]=""', '', request.body)
                txml = re.sub(r'NS[0-9]:', '', txml)
                request._body = txml
        style_name = os.path.basename(request.path)
        elm_user_style_title = style_name
        sld_body = None
        layer_name = None
        if 'name' in request.GET:
            style_name = request.GET['name']
            sld_body = request.body
        elif request.method == 'DELETE':
            style_name = os.path.basename(request.path)
        else:
            try:
                tree = ET.ElementTree(ET.fromstring(request.body))
                elm_namedlayer_name = tree.findall(
                    './/{http://www.opengis.net/sld}Name')[0]
                elm_user_style_name = tree.findall(
                    './/{http://www.opengis.net/sld}Name')[1]
                elm_user_style_title = tree.find(
                    './/{http://www.opengis.net/sld}Title')
                if not elm_user_style_title:
                    elm_user_style_title = elm_user_style_name.text
                layer_name = elm_namedlayer_name.text
                style_name = elm_user_style_name.text
                sld_body = '<?xml version="1.0" encoding="UTF-8"?>%s' % request.body
            except BaseException:
                logger.warn("Could not recognize Style and Layer name from Request!")
        # add style in GN and associate it to layer
        if request.method == 'DELETE':
            if style_name:
                try:
                    style = Style.objects.get(name=style_name)
                    style.delete()
                except BaseException:
                    pass
        if request.method == 'POST':
            if style_name:
                style, created = Style.objects.get_or_create(name=style_name)
                style.sld_body = sld_body
                style.sld_url = url
                style.save()
            layer = None
            if layer_name:
                try:
                    layer = Layer.objects.get(name=layer_name)
                except BaseException:
                    try:
                        layer = Layer.objects.get(alternate=layer_name)
                    except BaseException:
                        pass
            if layer:
                style.layer_styles.add(layer)
                style.save()
                affected_layers.append(layer)
        elif request.method == 'PUT':  # update style in GN
            if style_name:
                style, created = Style.objects.get_or_create(name=style_name)
                style.sld_body = sld_body
                style.sld_url = url
                if elm_user_style_title and len(elm_user_style_title) > 0:
                    style.sld_title = elm_user_style_title
                style.save()
                for layer in style.layer_styles.all():
                    layer.save()
                    affected_layers.append(layer)

        # Invalidate GeoWebCache so it doesn't retain old style in tiles
        try:
            _stylefilterparams_geowebcache_layer(layer_name)
            _invalidate_geowebcache_layer(layer_name)
        except BaseException:
            pass

    elif request.method == 'DELETE':  # delete style from GN
        style_name = os.path.basename(request.path)
        style = Style.objects.get(name=style_name)
        style.delete()

    return affected_layers


def set_time_info(layer, attribute, end_attribute, presentation,
                  precision_value, precision_step, enabled=True):
    '''Configure the time dimension for a layer.

    :param layer: the layer to configure
    :param attribute: the attribute used to represent the instant or period
                      start
    :param end_attribute: the optional attribute used to represent the end
                          period
    :param presentation: either 'LIST', 'DISCRETE_INTERVAL', or
                         'CONTINUOUS_INTERVAL'
    :param precision_value: number representing number of steps
    :param precision_step: one of 'seconds', 'minutes', 'hours', 'days',
                           'months', 'years'
    :param enabled: defaults to True
    '''
    layer = gs_catalog.get_layer(layer.name)
    if layer is None:
        raise ValueError('no such layer: %s' % layer.name)
    resource = layer.resource if layer else None
    if not resource:
        resources = gs_catalog.get_resources(store=layer.name)
        if resources:
            resource = resources[0]

    resolution = None
    if precision_value and precision_step:
        resolution = '%s %s' % (precision_value, precision_step)
    info = DimensionInfo("time", enabled, presentation, resolution, "ISO8601",
                         None, attribute=attribute, end_attribute=end_attribute)
    if resource and resource.metadata:
        metadata = dict(resource.metadata or {})
    else:
        metadata = dict({})
    metadata['time'] = info

    if resource and resource.metadata:
        resource.metadata = metadata
    if resource:
        gs_catalog.save(resource)


def get_time_info(layer):
    '''Get the configured time dimension metadata for the layer as a dict.

    The keys of the dict will be those of the parameters of `set_time_info`.

    :returns: dict of values or None if not configured
    '''
    layer = gs_catalog.get_layer(layer.name)
    if layer is None:
        raise ValueError('no such layer: %s' % layer.name)
    resource = layer.resource if layer else None
    if not resource:
        resources = gs_catalog.get_resources(store=layer.name)
        if resources:
            resource = resources[0]

    info = resource.metadata.get('time', None) if resource.metadata else None
    vals = None
    if info:
        value = step = None
        resolution = info.resolution_str()
        if resolution:
            value, step = resolution.split()
        vals = dict(
            enabled=info.enabled,
            attribute=info.attribute,
            end_attribute=info.end_attribute,
            presentation=info.presentation,
            precision_value=value,
            precision_step=step,
        )
    return vals


ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)['default']

_wms = None
_csw = None
_user, _password = ogc_server_settings.credentials

url = ogc_server_settings.rest
gs_catalog = Catalog(url, _user, _password)
gs_uploader = Client(url, _user, _password)

_punc = re.compile(r"[\.:]")  # regex for punctuation that confuses restconfig
_foregrounds = [
    "#ffbbbb",
    "#bbffbb",
    "#bbbbff",
    "#ffffbb",
    "#bbffff",
    "#ffbbff"]
_backgrounds = [
    "#880000",
    "#008800",
    "#000088",
    "#888800",
    "#008888",
    "#880088"]
_marks = ["square", "circle", "cross", "x", "triangle"]
_style_contexts = izip(cycle(_foregrounds), cycle(_backgrounds), cycle(_marks))
_default_style_names = ["point", "line", "polygon", "raster"]
_esri_types = {
    "esriFieldTypeDouble": "xsd:double",
    "esriFieldTypeString": "xsd:string",
    "esriFieldTypeSmallInteger": "xsd:int",
    "esriFieldTypeInteger": "xsd:int",
    "esriFieldTypeDate": "xsd:dateTime",
    "esriFieldTypeOID": "xsd:long",
    "esriFieldTypeGeometry": "xsd:geometry",
    "esriFieldTypeBlob": "xsd:base64Binary",
    "esriFieldTypeRaster": "raster",
    "esriFieldTypeGUID": "xsd:string",
    "esriFieldTypeGlobalID": "xsd:string",
    "esriFieldTypeXML": "xsd:anyType"}


def _render_thumbnail(req_body, width=240, height=180):
    spec = _fixup_ows_url(req_body)
    url = "%srest/printng/render.png" % ogc_server_settings.LOCATION
    hostname = urlparse(settings.SITEURL).hostname
    params = dict(width=width, height=height, auth="%s,%s,%s" % (hostname, _user, _password))
    url = url + "?" + urllib.urlencode(params)

    # @todo annoying but not critical
    # openlayers controls posted back contain a bad character. this seems
    # to come from a &minus; entity in the html, but it gets converted
    # to a unicode en-dash but is not uncoded properly during transmission
    # 'ignore' the error for now as controls are not being rendered...
    data = spec
    if isinstance(data, unicode):
        # make sure any stored bad values are wiped out
        # don't use keyword for errors - 2.6 compat
        # though unicode accepts them (as seen below)
        data = data.encode('ASCII', 'ignore')
    data = unicode(data, errors='ignore').encode('UTF-8')
    try:
        req, content = http_client.post(
            url, data=data, headers={'Content-type': 'text/html'})
    except BaseException:
        logging.warning('Error generating thumbnail')
        return
    return content


def _prepare_thumbnail_body_from_opts(request_body, request=None):
    import mercantile
    from geonode.utils import (_v,
                               bbox_to_projection,
                               bounds_to_zoom_level)
    if isinstance(request_body, basestring):
        request_body = json.loads(request_body)

    # Defaults
    _img_src_template = """<img src='{ogc_location}'
    style='width: {width}px; height: {height}px;
    left: {left}px; top: {top}px;
    opacity: 1; visibility: inherit; position: absolute;'/>\n"""

    def decimal_encode(bbox):
        import decimal
        _bbox = []
        for o in [float(coord) for coord in bbox]:
            if isinstance(o, decimal.Decimal):
                o = (str(o) for o in [o])
            _bbox.append(o)
        # Must be in the form : [x0, x1, y0, y1
        return [_bbox[0], _bbox[2], _bbox[1], _bbox[3]]

    # Sanity Checks
    if 'bbox' not in request_body:
        return None
    if 'srid' not in request_body:
        return None
    for coord in request_body['bbox']:
        if not coord:
            return None

    width = 240
    if 'width' in request_body:
        width = request_body['width']
    height = 200
    if 'height' in request_body:
        height = request_body['height']
    smurl = None
    if 'smurl' in request_body:
        smurl = request_body['smurl']
    if not smurl and getattr(settings, 'THUMBNAIL_GENERATOR_DEFAULT_BG', None):
        smurl = settings.THUMBNAIL_GENERATOR_DEFAULT_BG

    layers = None
    thumbnail_create_url = None
    if 'thumbnail_create_url' in request_body:
        thumbnail_create_url = request_body['thumbnail_create_url']
    elif 'layers' in request_body:
        layers = request_body['layers']

        wms_endpoint = getattr(ogc_server_settings, "WMS_ENDPOINT") or 'ows'
        wms_version = getattr(ogc_server_settings, "WMS_VERSION") or '1.1.1'
        wms_format = getattr(ogc_server_settings, "WMS_FORMAT") or 'image/png8'

        params = {
            'service': 'WMS',
            'version': wms_version,
            'request': 'GetMap',
            'layers': layers,
            'format': wms_format,
            # 'TIME': '-99999999999-01-01T00:00:00.0Z/99999999999-01-01T00:00:00.0Z'
        }

        if request and request.user:
            access_token = get_or_create_token(request.user)
            if access_token and not access_token.is_expired():
                params['access_token'] = access_token.token

        _p = "&".join("%s=%s" % item for item in params.items())

        import posixpath
        thumbnail_create_url = posixpath.join(
            ogc_server_settings.LOCATION,
            wms_endpoint) + "?" + _p

    # Compute Bounds
    wgs84_bbox = decimal_encode(
        bbox_to_projection([float(coord) for coord in request_body['bbox']] + [request_body['srid'], ],
                           target_srid=4326)[:4])

    # Fetch XYZ tiles - we are assuming Mercatore here
    bounds = wgs84_bbox[0:4]
    # Fixes bounds to tiles system
    bounds[0] = _v(bounds[0], x=True, target_srid=4326)
    bounds[2] = _v(bounds[2], x=True, target_srid=4326)
    if bounds[3] > 85.051:
        bounds[3] = 85.0
    if bounds[1] < -85.051:
        bounds[1] = -85.0
    if 'zoom' in request_body:
        zoom = request_body['zoom']
    else:
        zoom = bounds_to_zoom_level(bounds, width, height)

    t_ll = mercantile.tile(bounds[0], bounds[1], zoom)
    t_ur = mercantile.tile(bounds[2], bounds[3], zoom)

    numberOfRows = t_ll.y - t_ur.y + 1

    bounds_ll = mercantile.bounds(t_ll)
    bounds_ur = mercantile.bounds(t_ur)

    lat_res = abs(256 / (bounds_ur.north - bounds_ur.south))
    lng_res = abs(256 / (bounds_ll.east - bounds_ll.west))
    top = round(abs(bounds_ur.north - bounds[3]) * -lat_res)
    left = round(abs(bounds_ll.west - bounds[0]) * -lng_res)

    tmp_tile = mercantile.tile(bounds[0], bounds[3], zoom)
    width_acc = 256 + left
    first_row = [tmp_tile]
    # Add tiles to fill image width
    while width > width_acc:
        c = mercantile.ul(tmp_tile.x + 1, tmp_tile.y, zoom)
        lng = _v(c.lng, x=True, target_srid=4326)
        if lng == 180.0:
            lng = -180.0
        tmp_tile = mercantile.tile(lng, bounds[3], zoom)
        first_row.append(tmp_tile)
        width_acc = width_acc + 256

    # Build Image Request Template
    _img_request_template = "<div style='height:{height}px; width:{width}px;'>\
        <div style='position: absolute; top:{top}px; left:{left}px; z-index: 749; \
        transform: translate3d(0px, 0px, 0px) scale3d(1, 1, 1);'> \
        \n"                      .format(height=height, width=width, top=top, left=left)

    for row in range(0, numberOfRows):
        for col in range(0, len(first_row)):
            box = [col * 256, row * 256]
            t = first_row[col]
            y = t.y + row
            if smurl:
                imgurl = smurl.format(z=t.z, x=t.x, y=y)
                _img_request_template += _img_src_template.format(ogc_location=imgurl,
                                                                  height=256, width=256,
                                                                  left=box[0], top=box[1])
            xy_bounds = mercantile.xy_bounds(t.x, y, t.z)
            params = {
                'width': 256,
                'height': 256,
                'transparent': True,
                'bbox': ",".join([str(xy_bounds.left), str(xy_bounds.bottom),
                                  str(xy_bounds.right), str(xy_bounds.top)]),
                'crs': 'EPSG:3857',

            }
            _p = "&".join("%s=%s" % item for item in params.items())

            _img_request_template += \
                _img_src_template.format(ogc_location=(thumbnail_create_url + '&' + _p),
                                         height=256, width=256,
                                         left=box[0], top=box[1])
    _img_request_template += "</div></div>"
    image = _render_thumbnail(_img_request_template, width=width, height=height)
    return image


def _fixup_ows_url(thumb_spec):
    # @HACK - for whatever reason, a map's maplayers ows_url contains only /geoserver/wms
    # so rendering of thumbnails fails - replace those uri's with full geoserver URL
    import re
    gspath = '"' + ogc_server_settings.public_url  # this should be in img src attributes
    repl = '"' + ogc_server_settings.LOCATION
    return re.sub(gspath, repl, thumb_spec)


def mosaic_delete_first_granule(cat, layer):
    # - since GeoNode will uploade the first granule again through the Importer, we need to /
    #   delete the one created by the gs_config
    cat._cache.clear()
    store = cat.get_store(layer)
    coverages = cat.mosaic_coverages(store)

    granule_id = layer + ".1"

    cat.mosaic_delete_granule(coverages['coverages']['coverage'][0]['name'], store, granule_id)


def set_time_dimension(cat, name, workspace, time_presentation, time_presentation_res, time_presentation_default_value,
                       time_presentation_reference_value):
    # configure the layer time dimension as LIST
    cat._cache.clear()
    # cat.reload()

    presentation = time_presentation
    if not presentation:
        presentation = "LIST"

    resolution = None
    if time_presentation == 'DISCRETE_INTERVAL':
        resolution = time_presentation_res

    strategy = None
    if time_presentation_default_value and not time_presentation_default_value == "":
        strategy = time_presentation_default_value

    timeInfo = DimensionInfo("time", "true", presentation, resolution, "ISO8601", None, attribute="time",
                             strategy=strategy, reference_value=time_presentation_reference_value)

    layer = cat.get_layer(name)
    resource = layer.resource if layer else None
    if not resource:
        resources = cat.get_resources(store=name) or cat.get_resources(store=name, workspace=workspace)
        if resources:
            resource = resources[0]

    if not resource:
        logger.exception("No resource could be found on GeoServer with name %s" % name)
        raise Exception("No resource could be found on GeoServer with name %s" % name)

    resource.metadata = {'time': timeInfo}
    cat.save(resource)


# main entry point to create a thumbnail - will use implementation
# defined in settings.THUMBNAIL_GENERATOR (see settings.py)
def create_gs_thumbnail(instance, overwrite=False, check_bbox=False):
    implementation = import_string(settings.THUMBNAIL_GENERATOR)
    return implementation(instance, overwrite, check_bbox)
