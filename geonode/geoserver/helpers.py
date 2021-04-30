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
import os
import re
import sys
import time
import uuid
import json
import errno
import logging
import datetime
import tempfile
import traceback

from shutil import copyfile

from itertools import cycle
from decimal import Decimal
from collections import namedtuple, defaultdict
from os.path import basename, splitext, isfile
from threading import local
from urllib.parse import urlparse, urlencode, urlsplit, urljoin
from pinax.ratings.models import OverallRating
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
from defusedxml import lxml as dlxml
from owslib.wcs import WebCoverageService
from owslib.wms import WebMapService
from geonode import GeoNodeException
from geonode.utils import http_client
from geonode.layers.models import Layer, Attribute, Style
from geonode.layers.enumerations import LAYER_ATTRIBUTE_NUMERIC_DATA_TYPES
from geonode.security.views import _perms_info_json
from geonode.security.utils import set_geowebcache_invalidate_cache
import xml.etree.ElementTree as ET
from django.utils.module_loading import import_string


logger = logging.getLogger(__name__)

temp_style_name_regex = r'[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}_ms_.*'

if not hasattr(settings, 'OGC_SERVER'):
    msg = (
        'Please configure OGC_SERVER when enabling geonode.geoserver.'
        ' More info can be found at '
        'http://docs.geonode.org/en/2.10.x/basic/settings/index.html#ogc-server')
    raise ImproperlyConfigured(msg)


def check_geoserver_is_up():
    """Verifies all geoserver is running,
       this is needed to be able to upload.
    """
    url = f"{ogc_server_settings.LOCATION}"
    req, content = http_client.get(url, user=_user)
    msg = f'Cannot connect to the GeoServer at {url}\nPlease make sure you have started it.'
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
    return _punc.sub("_", f"{resource.store.workspace.name}:{resource.name}")


def extract_name_from_sld(gs_catalog, sld, sld_file=None):
    try:
        if sld:
            if isfile(sld):
                with open(sld, "rb") as sld_file:
                    sld = sld_file.read()
            if isinstance(sld, str):
                sld = sld.encode('utf-8')
            dom = etree.XML(sld)
        elif sld_file and isfile(sld_file):
            with open(sld_file, "rb") as sld_file:
                sld = sld_file.read()
            if isinstance(sld, str):
                sld = sld.encode('utf-8')
            dom = dlxml.parse(sld)
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
    name = None
    gs_layer = None
    gs_style = None

    _default_style = None
    _max_retries, _tries = getattr(ogc_server_settings, "MAX_RETRIES", 2), 0
    try:
        gs_layer = gs_catalog.get_layer(layer.name)
        if gs_layer.default_style:
            gs_style = gs_layer.default_style.sld_body
            set_layer_style(layer,
                            layer.alternate,
                            gs_style)
        name = gs_layer.default_style.name
        _default_style = gs_layer.default_style
    except Exception as e:
        logger.debug(e)
        name = None

    while not name and _tries < _max_retries:
        try:
            gs_layer = gs_catalog.get_layer(layer.name)
            if gs_layer:
                if gs_layer.default_style:
                    gs_style = gs_layer.default_style.sld_body
                    set_layer_style(layer,
                                    layer.alternate,
                                    gs_style)
                name = gs_layer.default_style.name
                if name:
                    break
        except Exception as e:
            logger.exception(e)
            name = None
        _tries += 1
        time.sleep(3)

    if not _default_style:
        _default_style = layer.default_style if layer else None
        name = _default_style.name if _default_style else None
        gs_style = _default_style.sld_body if _default_style else None

    if not name:
        msg = """
            GeoServer didn't return a default style for this layer.
            Consider increasing OGC_SERVER MAX_RETRIES value.''
        """
        raise GeoNodeException(msg)

    # Detect geometry type if it is a FeatureType
    res = gs_layer.resource if gs_layer else None
    if res and res.resource_type == 'featureType':
        res.fetch()
        ft = res.store.get_resources(name=res.name)
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
        fg, bg, mark = next(_style_contexts)
        return _style_templates[name] % dict(
            name=layer.name,
            fg=fg,
            bg=bg,
            mark=mark)
    else:
        return gs_style


def set_layer_style(saved_layer, title, sld, base_file=None):
    # Check SLD is valid
    try:
        if sld:
            if isfile(sld):
                with open(sld, "rb") as sld_file:
                    sld = sld_file.read()

            elif isinstance(sld, str):
                sld = sld.strip('b\'\n')
                sld = re.sub(r'(\\r)|(\\n)', '', sld).encode("UTF-8")
            etree.XML(sld)
        elif base_file and isfile(base_file):
            with open(base_file, "rb") as sld_file:
                sld = sld_file.read()
            dlxml.parse(base_file)
    except Exception:
        logger.exception("The uploaded SLD file is not valid XML")
        raise Exception("The uploaded SLD file is not valid XML")

    # Check Layer's available styles
    match = None
    styles = list(saved_layer.styles.all()) + [
        saved_layer.default_style]
    for style in styles:
        if style and style.name == saved_layer.name:
            match = style
            break
    layer = gs_catalog.get_layer(title)
    style = None
    if match is None:
        try:
            style = gs_catalog.get_style(saved_layer.name, workspace=saved_layer.workspace) or \
                gs_catalog.get_style(saved_layer.name)
            if not style:
                style = gs_catalog.create_style(
                    saved_layer.name, sld, overwrite=False, raw=True, workspace=saved_layer.workspace)
        except Exception as e:
            logger.exception(e)
    else:
        style = gs_catalog.get_style(saved_layer.name, workspace=saved_layer.workspace) or \
            gs_catalog.get_style(saved_layer.name)
        try:
            if not style:
                style = gs_catalog.create_style(
                    saved_layer.name, sld,
                    overwrite=True, raw=True,
                    workspace=saved_layer.workspace)
            elif sld:
                style.update_body(sld)
        except Exception as e:
            logger.exception(e)

    if layer and style:
        _old_styles = []
        _old_styles.append(gs_catalog.get_style(
            name=saved_layer.name))
        _old_styles.append(gs_catalog.get_style(
            name=f"{saved_layer.workspace}_{saved_layer.name}"))
        _old_styles.append(gs_catalog.get_style(
            name=layer.default_style.name))
        _old_styles.append(gs_catalog.get_style(
            name=layer.default_style.name,
            workspace=layer.default_style.workspace))
        layer.default_style = style
        gs_catalog.save(layer)
        for _s in _old_styles:
            try:
                gs_catalog.delete(_s)
            except Exception as e:
                logger.debug(e)
        set_styles(saved_layer, gs_catalog)


def cascading_delete(layer_name=None, catalog=None):
    if not layer_name:
        return
    cat = catalog or gs_catalog
    resource = None
    workspace = None
    try:
        if layer_name.find(':') != -1 and len(layer_name.split(':')) == 2:
            workspace, name = layer_name.split(':')
            ws = cat.get_workspace(workspace)
            store = None
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
                else:
                    logger.debug(
                        'the store was not found in geoserver')
            if ws is None or store is None:
                logger.debug(
                    'cascading delete was called on a layer where the workspace was not found')
            resource = cat.get_resource(name=name, store=store, workspace=workspace)
        else:
            resource = cat.get_resource(name=layer_name)
    except EnvironmentError as e:
        if e.errno == errno.ECONNREFUSED:
            msg = ('Could not connect to geoserver at "%s"'
                   'to save information for layer "%s"' % (
                       ogc_server_settings.LOCATION, layer_name)
                   )
            logger.error(msg)
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
    lyr = None
    try:
        lyr = cat.get_layer(resource_name)
    except Exception as e:
        logger.debug(e)
    if lyr is not None:  # Already deleted
        store = resource.store
        styles = lyr.styles
        try:
            styles = styles + [lyr.default_style]
        except Exception:
            pass
        if workspace:
            gs_styles = [x for x in cat.get_styles(names=[f"{workspace}_{resource_name}"])]
            styles = styles + gs_styles
        if settings.DEFAULT_WORKSPACE and settings.DEFAULT_WORKSPACE != workspace:
            gs_styles = [x for x in cat.get_styles(names=[f"{settings.DEFAULT_WORKSPACE}_{resource_name}"])]
            styles = styles + gs_styles
        cat.delete(lyr)
        for s in styles:
            if s is not None and s.name not in _default_style_names:
                try:
                    logger.debug(f"Trying to delete Style [{s.name}]")
                    cat.delete(s, purge='true')
                except Exception as e:
                    # Trying to delete a shared style will fail
                    # We'll catch the exception and log it.
                    logger.debug(e)

        # Due to a possible bug of geoserver, we need this trick for now
        # TODO: inspect the issue reported by this hack. Should be solved
        #       with GS 2.7+
        try:
            cat.delete(resource, recurse=True)  # This may fail
        except Exception:
            cat._cache.clear()
            cat.reset()

        if store.resource_type == 'dataStore' and 'dbtype' in store.connection_parameters and \
                store.connection_parameters['dbtype'] == 'postgis':
            delete_from_postgis(resource_name, store)
        else:
            if store.resource_type == 'coverageStore':
                try:
                    logger.debug(f" - Going to purge the {store.resource_type} : {store.href}")
                    cat.reset()  # this resets the coverage readers and unlocks the files
                    cat.delete(store, purge='all', recurse=True)
                    # cat.reload()  # this preservers the integrity of geoserver
                except Exception as e:
                    # Trying to recursively purge a store may fail
                    # We'll catch the exception and log it.
                    logger.debug(e)
            else:
                try:
                    if not store.get_resources():
                        cat.delete(store, recurse=True)
                except Exception as e:
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
        cur.execute(f"SELECT DropGeometryTable ('{layer_name}')")
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
        print("Inspecting the available layers in GeoServer ...", file=console)

    cat = gs_catalog

    if workspace is not None and workspace:
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
                    resources = cat.get_resources(stores=[store])
            else:
                resources = cat.get_resources(workspaces=[workspace])
    elif store is not None:
        store = get_store(cat, store)
        resources = cat.get_resources(stores=[store])
    else:
        resources = cat.get_resources()

    if remove_deleted:
        resources_for_delete_compare = resources[:]
        workspace_for_delete_compare = workspace
        # filter out layers for delete comparison with GeoNode layers by following criteria:
        # enabled = true, if --skip-unadvertised: advertised = true, but
        # disregard the filter parameter in the case of deleting layers
        try:
            resources_for_delete_compare = [
                k for k in resources_for_delete_compare if k.enabled in {"true", True}]
            if skip_unadvertised:
                resources_for_delete_compare = [
                    k for k in resources_for_delete_compare if k.advertised in {"true", True}]
        except Exception:
            if ignore_errors:
                pass
            else:
                raise

    if filter:
        resources = [k for k in resources if filter in k.name]

    # filter out layers depending on enabled, advertised status:
    _resources = []
    for k in resources:
        try:
            if k.enabled in {"true", True}:
                _resources.append(k)
        except Exception:
            if ignore_errors:
                continue
            else:
                raise
    # resources = [k for k in resources if k.enabled in {"true", True}]
    resources = _resources
    if skip_unadvertised:
        try:
            resources = [k for k in resources if k.advertised in {"true", True}]
        except Exception:
            if ignore_errors:
                pass
            else:
                raise

    # filter out layers already registered in geonode
    layer_names = Layer.objects.all().values_list('alternate', flat=True)
    if skip_geonode_registered:
        try:
            resources = [k for k in resources
                         if f'{k.workspace.name}:{k.name}' not in layer_names]
        except Exception:
            if ignore_errors:
                pass
            else:
                raise

    # TODO: Should we do something with these?
    # i.e. look for matching layers in GeoNode and also disable?
    # disabled_resources = [k for k in resources if k.enabled == "false"]

    number = len(resources)
    if verbosity > 0:
        msg = "Found %d layers, starting processing" % number
        print(msg, file=console)
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
            created = False
            layer = Layer.objects.filter(name=name, workspace=workspace.name).first()
            if not layer:
                layer = Layer.objects.create(
                    name=name,
                    workspace=workspace.name,
                    store=the_store.name,
                    storeType=the_store.resource_type,
                    alternate=f"{workspace.name}:{resource.name}",
                    title=resource.title or 'No title provided',
                    abstract=resource.abstract or "{}".format(_('No abstract provided')),
                    owner=owner,
                    uuid=str(uuid.uuid4())
                )
                created = True
            layer.bbox_x0 = Decimal(resource.native_bbox[0])
            layer.bbox_x1 = Decimal(resource.native_bbox[1])
            layer.bbox_y0 = Decimal(resource.native_bbox[2])
            layer.bbox_y1 = Decimal(resource.native_bbox[3])
            layer.srid = resource.projection

            # sync permissions in GeoFence
            perm_spec = json.loads(_perms_info_json(layer))
            layer.set_permissions(perm_spec)

            # recalculate the layer statistics
            set_attributes_from_geoserver(layer, overwrite=True)

            # in some cases we need to explicitily save the resource to execute the signals
            # (for sure when running updatelayers)
            if execute_signals:
                layer.save(notify=True)

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
                    print(msg, file=sys.stderr)

                raise Exception(f"Failed to process {resource.name}") from e

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
            print(msg, file=console)

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
            print(msg, file=console)

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
            except Exception:
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
                print(msg, file=console)

    finish = datetime.datetime.now(timezone.get_current_timezone())
    td = finish - start
    output['stats']['duration_sec'] = td.microseconds / \
        1000000 + td.seconds + td.days * 24 * 3600
    return output


def get_stores(store_type=None):
    cat = gs_catalog
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
        if len(attribute) == 2:
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
                attribute[attribute_map_dict['display_order']] = la.display_order
        if overwrite or not lafound:
            logger.debug(
                "Going to delete [%s] for [%s]",
                la.attribute,
                layer.name)
            la.delete()

    # Add new layer attributes if they doesn't exist already
    if attribute_map:
        iter = len(Attribute.objects.filter(layer=layer)) + 1
        for attribute in attribute_map:
            field, ftype, description, label, display_order = attribute
            if field:
                _gs_attrs = Attribute.objects.filter(layer=layer, attribute=field)
                if _gs_attrs.count() == 1:
                    la = _gs_attrs.get()
                else:
                    if _gs_attrs.count() > 0:
                        _gs_attrs.delete()
                    la = Attribute.objects.create(layer=layer, attribute=field)
                    la.visible = ftype.find("gml:") != 0
                    la.attribute_type = ftype
                    la.description = description
                    la.attribute_label = label
                    la.display_order = iter
                    iter += 1
                if (not attribute_stats or layer.name not in attribute_stats or
                        field not in attribute_stats[layer.name]):
                    result = None
                else:
                    result = attribute_stats[layer.name][field]
                if result:
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
                try:
                    la.save()
                except Exception as e:
                    logger.exception(e)
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
        dft_url = server_url + ("%s?f=json" % (layer.alternate or layer.typename))
        try:
            # The code below will fail if http_client cannot be imported
            req, body = http_client.get(dft_url, user=_user)
            body = json.loads(body)
            attribute_map = [[n["name"], _esri_types[n["type"]]]
                             for n in body["fields"] if n.get("name") and n.get("type")]
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            attribute_map = []
    elif layer.storeType in {"dataStore", "remoteStore", "wmsStore"}:
        typename = layer.alternate if layer.alternate else layer.typename
        dft_url = re.sub(r"\/wms\/?$",
                         "/",
                         server_url) + "ows?" + urlencode({"service": "wfs",
                                                           "version": "1.0.0",
                                                           "request": "DescribeFeatureType",
                                                           "typename": typename,
                                                           })
        try:
            # The code below will fail if http_client cannot be imported or WFS not supported
            req, body = http_client.get(dft_url, user=_user)
            doc = dlxml.fromstring(body.encode())
            path = ".//{xsd}extension/{xsd}sequence/{xsd}element".format(
                xsd="{http://www.w3.org/2001/XMLSchema}")
            attribute_map = [[n.attrib["name"], n.attrib["type"]] for n in doc.findall(
                path) if n.attrib.get("name") and n.attrib.get("type")]
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            attribute_map = []
            # Try WMS instead
            dft_url = server_url + "?" + urlencode({
                "service": "wms",
                "version": "1.0.0",
                "request": "GetFeatureInfo",
                "bbox": ','.join([str(x) for x in layer.bbox]),
                "LAYERS": layer.alternate,
                "QUERY_LAYERS": typename,
                "feature_count": 1,
                "width": 1,
                "height": 1,
                "srs": "EPSG:4326",
                "info_format": "text/html",
                "x": 1,
                "y": 1
            })
            try:
                req, body = http_client.get(dft_url, user=_user)
                soup = BeautifulSoup(body, features="lxml")
                for field in soup.findAll('th'):
                    if(field.string is None):
                        field_name = field.contents[0].string
                    else:
                        field_name = field.string
                    attribute_map.append([field_name, "xsd:string"])
            except Exception:
                tb = traceback.format_exc()
                logger.debug(tb)
                attribute_map = []
    elif layer.storeType in ["coverageStore"]:
        typename = layer.alternate if layer.alternate else layer.typename
        dc_url = server_url + "wcs?" + urlencode({
            "service": "wcs",
            "version": "1.1.0",
            "request": "DescribeCoverage",
            "identifiers": typename
        })
        try:
            req, body = http_client.get(dc_url, user=_user)
            doc = dlxml.fromstring(body.encode())
            path = ".//{wcs}Axis/{wcs}AvailableKeys/{wcs}Key".format(
                wcs="{http://www.opengis.net/wcs/1.1.1}")
            attribute_map = [[n.text, "raster"] for n in doc.findall(path)]
        except Exception:
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
            elif is_layer_attribute_aggregable(
                    layer.storeType,
                    field,
                    ftype):
                logger.debug("Generating layer attribute statistics")
                result = get_attribute_statistics(layer.alternate or layer.typename, field)
            else:
                result = None
            attribute_stats[layer.name][field] = result
    set_attributes(
        layer, attribute_map, overwrite=overwrite, attribute_stats=attribute_stats
    )


def set_styles(layer, gs_catalog):
    style_set = []
    gs_layer = None
    try:
        gs_layer = gs_catalog.get_layer(layer.name)
    except Exception:
        tb = traceback.format_exc()
        logger.exception(tb)

    if not gs_layer:
        try:
            gs_layer = gs_catalog.get_layer(layer.alternate or layer.typename)
        except Exception:
            tb = traceback.format_exc()
            logger.error(tb)
            logger.exception("No GeoServer Layer found!")

    if gs_layer:
        default_style = gs_catalog.get_style(
            name=gs_layer.default_style.name,
            workspace=gs_layer.default_style.workspace)
        if default_style:
            # make sure we are not using a default SLD (which won't be editable)
            layer.default_style = save_style(default_style, layer)
            style_set.append(layer.default_style)

        try:
            if gs_layer.styles:
                alt_styles = gs_layer.styles
                for alt_style in alt_styles:
                    if alt_style and alt_style:
                        _s = save_style(alt_style, layer)
                        if _s != layer.default_style:
                            style_set.append(_s)
        except Exception as e:
            logger.exception(e)

    if style_set:
        # Remove duplicates
        style_set = list(dict.fromkeys(style_set))
        layer.styles.set(style_set)

    # Update default style to database
    to_update = {
        'default_style': layer.default_style
    }

    Layer.objects.filter(id=layer.id).update(**to_update)
    layer.refresh_from_db()

    # Legend links
    logger.debug(" -- Resource Links[Legend link]...")
    try:
        from geonode.base.models import Link
        layer_legends = Link.objects.filter(resource=layer.resourcebase_ptr, name='Legend')
        for style in set(list(layer.styles.all()) + [layer.default_style, ]):
            if style:
                style_name = os.path.basename(
                    urlparse(style.sld_url).path).split('.')[0]
                legend_url = ogc_server_settings.PUBLIC_LOCATION + \
                    'ows?service=WMS&request=GetLegendGraphic&format=image/png&WIDTH=20&HEIGHT=20&LAYER=' + \
                    layer.alternate + '&STYLE=' + style_name + \
                    '&legend_options=fontAntiAliasing:true;fontSize:12;forceLabels:on'
                if layer_legends.filter(resource=layer.resourcebase_ptr,
                                        name='Legend',
                                        url=legend_url).count() < 2:
                    Link.objects.update_or_create(
                        resource=layer.resourcebase_ptr,
                        name='Legend',
                        url=legend_url,
                        defaults=dict(
                            extension='png',
                            url=legend_url,
                            mime='image/png',
                            link_type='image',
                        )
                    )
        logger.debug(" -- Resource Links[Legend link]...done!")
    except Exception as e:
        logger.debug(f" -- Resource Links[Legend link]...error: {e}")

    try:
        set_geowebcache_invalidate_cache(layer.alternate or layer.typename, cat=gs_catalog)
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)


def save_style(gs_style, layer):
    style_name = os.path.basename(
        urlparse(gs_style.body_href).path).split('.')[0]
    sld_name = gs_style.name
    sld_body = gs_style.sld_body
    if not gs_style.workspace:
        gs_style = gs_catalog.create_style(
            style_name, sld_body,
            raw=True, overwrite=True,
            workspace=layer.workspace)

    style = None
    try:
        style, created = Style.objects.get_or_create(name=style_name)
        style.workspace = gs_style.workspace
        style.sld_title = gs_style.sld_title if gs_style.style_format != 'css' and gs_style.sld_title else sld_name
        style.sld_body = gs_style.sld_body
        style.sld_url = gs_style.body_href
        style.save()
    except Exception as e:
        tb = traceback.format_exc()
        logger.debug(tb)
        raise e
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
    if field_name.lower() in {'id', 'identifier'}:
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
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)
        logger.exception('Error generating layer aggregate statistics')


def get_wcs_record(instance, retry=True):
    wcs = WebCoverageService(f"{ogc_server_settings.LOCATION}wcs", '1.0.0')
    key = f"{instance.workspace}:{instance.name}"
    logger.debug(wcs.contents)
    if key in wcs.contents:
        return wcs.contents[key]
    else:
        msg = (f"Layer '{key}' was not found in WCS service at {ogc_server_settings.public_url}."
               )
        if retry:
            logger.debug(
                f"{msg} Waiting a couple of seconds before trying again.")
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
    except Layer.DoesNotExist:
        pass
    else:
        msg = f'Not doing any cleanup because the layer {name} exists in the Django db.'
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
        except Exception:
            logger.warning("Couldn't delete GeoServer layer during cleanup()")
    if gs_resource is not None:
        try:
            cat.delete(gs_resource)
        except Exception:
            msg = 'Couldn\'t delete GeoServer resource during cleanup()'
            logger.warning(msg)
    if gs_store is not None:
        try:
            cat.delete(gs_store)
        except Exception:
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
            ds = cat.get_store(dsname, workspace=workspace)
        else:
            return None
        if ds is None:
            raise FailedRequestError
        ds_exists = True
    except FailedRequestError:
        logger.debug(
            f'Creating target datastore {dsname}')
        ds = cat.create_datastore(dsname, workspace=workspace)
        db = ogc_server_settings.datastore_db
        db_engine = 'postgis' if \
            'postgis' in db['ENGINE'] else db['ENGINE']
        ds.connection_parameters.update(
            {'Evictor run periodicity': 300,
             'Estimated extends': 'true',
             'fetch size': 100000,
             'encode functions': 'false',
             'Expose primary keys': 'true',
             'validate connections': 'true',
             'Support on the fly geometry simplification': 'false',
             'Connection timeout': 10,
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
                 db['PORT'], str) else str(db['PORT']) or '5432',
             'database': db['NAME'],
             'user': db['USER'],
             'passwd': db['PASSWORD'],
             'dbtype': db_engine}
        )

    if ds_exists:
        ds.save_method = "PUT"

    logger.debug('Updating target datastore % s' % dsname)
    cat.save(ds)

    logger.debug('Reloading target datastore % s' % dsname)
    ds = get_store(cat, dsname, workspace=workspace)
    assert ds.enabled

    return ds


def _create_featurestore(name, data, overwrite=False, charset="UTF-8", workspace=None):

    cat = gs_catalog
    cat.create_featurestore(name, data, workspace=workspace, overwrite=overwrite, charset=charset)
    store = get_store(cat, name, workspace=workspace)
    return store, cat.get_resource(name=name, store=store, workspace=workspace)


def _create_coveragestore(name, data, overwrite=False, charset="UTF-8", workspace=None):
    cat = gs_catalog
    cat.create_coveragestore(name, path=data, workspace=workspace, overwrite=overwrite, upload_data=True)
    store = get_store(cat, name, workspace=workspace)
    return store, cat.get_resource(name=name, store=store, workspace=workspace)


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
        resource = cat.get_resource(name=name, store=ds, workspace=workspace)
        assert resource is not None
        return ds, resource
    except Exception:
        msg = _("An exception occurred loading data to PostGIS")
        msg += f"- {sys.exc_info()[1]}"
        try:
            delete_from_postgis(name, ds)
        except Exception:
            msg += _(" Additionally an error occured during database cleanup")
            msg += f"- {sys.exc_info()[1]}"
        raise GeoNodeException(msg)


def get_store(cat, name, workspace=None):
    # Make sure workspace is a workspace object and not a string.
    # If the workspace does not exist, continue as if no workspace had been defined.
    if isinstance(workspace, str):
        workspace = cat.get_workspace(workspace)

    if workspace is None:
        workspace = cat.get_default_workspace()

    if workspace:
        try:
            store = cat.get_xml(f'{workspace.datastore_url[:-4]}/{name}.xml')
        except FailedRequestError:
            try:
                store = cat.get_xml(f'{workspace.coveragestore_url[:-4]}/{name}.xml')
            except FailedRequestError:
                try:
                    store = cat.get_xml(f'{workspace.wmsstore_url[:-4]}/{name}.xml')
                except FailedRequestError:
                    raise FailedRequestError(f"No store found named: {name}")
        if store:
            if store.tag == 'dataStore':
                store = datastore_from_index(cat, workspace, store)
            elif store.tag == 'coverageStore':
                store = coveragestore_from_index(cat, workspace, store)
            elif store.tag == 'wmsStore':
                store = wmsstore_from_index(cat, workspace, store)
            return store
        else:
            raise FailedRequestError(f"No store found named: {name}")
    else:
        raise FailedRequestError(f"No store found named: {name}")


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
    def hostname(self):
        return urlsplit(self.LOCATION).hostname

    @property
    def netloc(self):
        return urlsplit(self.LOCATION).netloc

    def __str__(self):
        return f"{self.alias}"


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
            raise ServerDoesNotExist(f"The server {alias} doesn't exist")

        if 'PRINTNG_ENABLED' in server:
            raise ImproperlyConfigured("The PRINTNG_ENABLED setting has been removed, use 'PRINT_NG_ENABLED' instead.")

    def ensure_defaults(self, alias):
        """
        Puts the defaults into the settings dictionary for a given connection where no settings is provided.
        """
        try:
            server = self.servers[alias]
        except KeyError:
            raise ServerDoesNotExist(f"The server {alias} doesn't exist")

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


def fetch_gs_resource(instance, values, tries):
    _max_tries = getattr(ogc_server_settings, "MAX_RETRIES", 2)
    try:
        gs_resource = gs_catalog.get_resource(
            name=instance.name,
            store=instance.store,
            workspace=instance.workspace)
    except Exception:
        try:
            gs_resource = gs_catalog.get_resource(
                name=instance.alternate,
                store=instance.store,
                workspace=instance.workspace)
        except Exception:
            try:
                gs_resource = gs_catalog.get_resource(
                    name=instance.alternate or instance.typename)
            except Exception:
                gs_resource = None
    if gs_resource:
        if values:
            gs_resource.title = values.get('title', '')
            gs_resource.abstract = values.get('abstract', '')
        else:
            values = {}
        values.update(dict(store=gs_resource.store.name,
                           storeType=gs_resource.store.resource_type,
                           alternate=f"{gs_resource.store.workspace.name}:{gs_resource.name}",
                           title=gs_resource.title or gs_resource.store.name,
                           abstract=gs_resource.abstract or '',
                           owner=instance.owner))
    else:
        msg = f"There isn't a geoserver resource for this layer: {instance.name}"
        logger.exception(msg)
        if tries >= _max_tries:
            # raise GeoNodeException(msg)
            return (values, None)
        gs_resource = None
        time.sleep(5)
    return (values, gs_resource)


def get_wms():
    wms_url = f"{ogc_server_settings.internal_ows}?service=WMS&request=GetCapabilities&version=1.1.0"
    req, body = http_client.get(wms_url, user=_user)
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
        headers=headers,
        user=_user,
        timeout=5,
        retries=1)

    exml = dlxml.fromstring(content.encode())

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
    url = f'{ogc_server_settings.LOCATION}gwc/rest/layers/{layer_name}.xml'

    # read GWC configuration
    req, content = http_client.get(
        url,
        headers=headers,
        user=_user)
    if req.status_code != 200:
        line = f"Error {req.status_code} reading Style Filter Params GeoWebCache at {url}"
        logger.error(line)
        return

    # check/write GWC filter parameters
    body = None
    tree = dlxml.fromstring(_)
    param_filters = tree.findall('parameterFilters')
    if param_filters and len(param_filters) > 0:
        if not param_filters[0].findall('styleParameterFilter'):
            style_filters_xml = "<styleParameterFilter><key>STYLES</key>\
                <defaultValue></defaultValue></styleParameterFilter>"
            style_filters_elem = dlxml.fromstring(style_filters_xml)
            param_filters[0].append(style_filters_elem)
            body = ET.tostring(tree)
    if body:
        req, content = http_client.post(
            url,
            data=body,
            headers=headers,
            user=_user)
        if req.status_code != 200:
            line = f"Error {req.status_code} writing Style Filter Params GeoWebCache at {url}"
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
        url = f'{ogc_server_settings.LOCATION}gwc/rest/masstruncate'
    req, content = http_client.post(
        url,
        data=body,
        headers=headers,
        user=_user)

    if req.status_code != 200:
        line = f"Error {req.status_code} invalidating GeoWebCache at {url}"
        logger.debug(line)


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
                tree = ET.ElementTree(dlxml.fromstring(request.body))
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
                sld_body = f'<?xml version="1.0" encoding="UTF-8"?>{request.body}'
            except Exception:
                logger.warn("Could not recognize Style and Layer name from Request!")
        # add style in GN and associate it to layer
        if request.method == 'DELETE':
            if style_name:
                Style.objects.filter(name=style_name).delete()
        if request.method == 'POST':
            style = None
            if style_name and not re.match(temp_style_name_regex, style_name):
                style, created = Style.objects.get_or_create(name=style_name)
                style.sld_body = sld_body
                style.sld_url = url
                style.save()
            layer = None
            if layer_name:
                try:
                    layer = Layer.objects.get(name=layer_name)
                except Exception:
                    try:
                        layer = Layer.objects.get(alternate=layer_name)
                    except Exception:
                        pass
            if layer:
                if style:
                    style.layer_styles.add(layer)
                    style.save()
                affected_layers.append(layer)
        elif request.method == 'PUT':  # update style in GN
            if style_name and not re.match(temp_style_name_regex, style_name):
                style, created = Style.objects.get_or_create(name=style_name)
                style.sld_body = sld_body
                style.sld_url = url
                if elm_user_style_title and len(elm_user_style_title) > 0:
                    style.sld_title = elm_user_style_title
                style.save()
                for layer in style.layer_styles.all():
                    affected_layers.append(layer)

        # Invalidate GeoWebCache so it doesn't retain old style in tiles
        try:
            _stylefilterparams_geowebcache_layer(layer_name)
            _invalidate_geowebcache_layer(layer_name)
        except Exception:
            pass
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
        raise ValueError(f'no such layer: {layer.name}')
    resource = layer.resource if layer else None
    if not resource:
        resources = gs_catalog.get_resources(stores=[layer.name])
        if resources:
            resource = resources[0]

    resolution = None
    if precision_value and precision_step:
        resolution = f'{precision_value} {precision_step}'
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
        raise ValueError(f'no such layer: {layer.name}')
    resource = layer.resource if layer else None
    if not resource:
        resources = gs_catalog.get_resources(stores=[layer.name])
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
gs_catalog = Catalog(url, _user, _password,
                     retries=ogc_server_settings.MAX_RETRIES,
                     backoff_factor=ogc_server_settings.BACKOFF_FACTOR)
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
_style_contexts = zip(cycle(_foregrounds), cycle(_backgrounds), cycle(_marks))
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


def _dump_image_spec(request_body, image_spec):
    millis = int(round(time.time() * 1000))
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            _request_body_file_name = os.path.join(
                tmp_dir,
                f"request_body_{millis}.dump")
            _image_spec_file_name = os.path.join(
                tmp_dir,
                f"image_spec_{millis}.dump")
            with open(_request_body_file_name, "w") as _request_body_file:
                _request_body_file.write(f"{request_body}")
            copyfile(
                _request_body_file_name,
                os.path.join(tempfile.gettempdir(), f"request_body_{millis}.dump"))
            with open(_image_spec_file_name, "w") as _image_spec_file:
                _image_spec_file.write(f"{image_spec}")
            copyfile(
                _image_spec_file_name,
                os.path.join(tempfile.gettempdir(), f"image_spec_{millis}.dump"))
        return f"Dumping image_spec to: {os.path.join(tempfile.gettempdir(), f'image_spec_{millis}.dump')}"
    except Exception as e:
        logger.exception(e)
        return f"Unable to dump image_spec for request: {request_body}"


def _fixup_ows_url(thumb_spec):
    # @HACK - for whatever reason, a map's maplayers ows_url contains only /geoserver/wms
    # so rendering of thumbnails fails - replace those uri's with full geoserver URL
    gspath = f"\"{ogc_server_settings.public_url}"  # this should be in img src attributes
    repl = f"\"{ogc_server_settings.LOCATION}"
    return re.sub(gspath, repl, thumb_spec)


def mosaic_delete_first_granule(cat, layer):
    # - since GeoNode will uploade the first granule again through the Importer, we need to /
    #   delete the one created by the gs_config
    cat._cache.clear()
    store = cat.get_store(layer)
    coverages = cat.mosaic_coverages(store)

    granule_id = f"{layer}.1"

    cat.mosaic_delete_granule(coverages['coverages']['coverage'][0]['name'], store, granule_id)


def set_time_dimension(cat, name, workspace, time_presentation, time_presentation_res, time_presentation_default_value,
                       time_presentation_reference_value):
    # configure the layer time dimension as LIST
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
        resources = cat.get_resources(stores=[name]) or cat.get_resources(stores=[name], workspaces=[workspace])
        if resources:
            resource = resources[0]

    if not resource:
        logger.exception(f"No resource could be found on GeoServer with name {name}")
        raise Exception(f"No resource could be found on GeoServer with name {name}")

    resource.metadata = {'time': timeInfo}
    cat.save(resource)


# main entry point to create a thumbnail - will use implementation
# defined in settings.THUMBNAIL_GENERATOR (see settings.py)
def create_gs_thumbnail(instance, overwrite=False, check_bbox=False):
    implementation = import_string(settings.THUMBNAIL_GENERATOR)
    return implementation(instance, overwrite, check_bbox)
