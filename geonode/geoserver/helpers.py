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
import copy
import time
import uuid
import json
import errno
import typing
import logging
import datetime
import tempfile
import traceback
import dataclasses

from shutil import copyfile
from itertools import cycle
from collections import defaultdict
from os.path import basename, splitext, isfile
from urllib.parse import urlparse, urlencode, urlsplit, urljoin
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.utils.module_loading import import_string
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from geoserver.catalog import Catalog, FailedRequestError
from geoserver.resource import FeatureType, Coverage
from geoserver.store import (
    CoverageStore,
    DataStore,
    datastore_from_index,
    coveragestore_from_index,
    wmsstore_from_index,
)
from geoserver.support import DimensionInfo
from geoserver.workspace import Workspace
from gsimporter import Client
from lxml import etree, objectify
from owslib.etree import etree as dlxml
from owslib.wcs import WebCoverageService

from geonode import GeoNodeException
from geonode.base.models import Link
from geonode.base.models import ResourceBase
from geonode.security.views import _perms_info_json
from geonode.catalogue.models import catalogue_post_save
from geonode.layers.models import Dataset, Attribute, Style
from geonode.layers.enumerations import LAYER_ATTRIBUTE_NUMERIC_DATA_TYPES

from geonode.utils import (
    OGC_Servers_Handler,
    http_client,
    get_legend_url,
    is_monochromatic_image,
    set_resource_default_links,
)

from .geofence import GeoFenceClient, GeoFenceUtils

logger = logging.getLogger(__name__)

temp_style_name_regex = r"[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}_ms_.*"

LAYER_SUBTYPES = {
    "dataStore": "vector",
    "coverageStore": "raster",
    "remoteStore": "remote",
    "vectorTimeSeries": "vector_time",
}

WPS_ACCEPTABLE_FORMATS = [
    ("application/json", "vector"),
    ("application/arcgrid", "raster"),
    ("image/tiff", "raster"),
    ("image/png", "raster"),
    ("image/jpeg", "raster"),
    ("application/wfs-collection-1.0", "vector"),
    ("application/wfs-collection-1.1", "vector"),
    ("application/zip", "vector"),
    ("text/csv", "vector"),
]

DEFAULT_STYLE_NAME = ["generic", "line", "point", "polygon", "raster"]


if not hasattr(settings, "OGC_SERVER"):
    msg = (
        "Please configure OGC_SERVER when enabling geonode.geoserver."
        " More info can be found at "
        "http://docs.geonode.org/en/2.10.x/basic/settings/index.html#ogc-server"
    )
    raise ImproperlyConfigured(msg)


def check_geoserver_is_up():
    """Verifies all geoserver is running,
    this is needed to be able to upload.
    """
    url = f"{ogc_server_settings.LOCATION}"
    req, content = http_client.get(url, user=_user)
    msg = f"Cannot connect to the GeoServer at {url}\nPlease make sure you have started it."
    logger.debug(req)
    assert req.status_code == 200, msg


def _add_sld_boilerplate(symbolizer):
    """
    Wrap an XML snippet representing a single symbolizer in the appropriate
    elements to make it a valid SLD which applies that symbolizer to all features,
    including format strings to allow interpolating a "name" variable in.
    """
    return (
        """
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
"""
        + symbolizer
        + """
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
"""
    )


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
    point=_add_sld_boilerplate(_point_template),
)

STYLES_VERSION = {"1.0.0": "sld10", "1.1.0": "sld11"}


def _extract_style_version_from_sld(sld):
    """
    Assume: SLD as a byte
    """
    root = objectify.fromstring(sld)
    try:
        return STYLES_VERSION[root.attrib["version"].strip()]
    except Exception:
        return STYLES_VERSION["1.0.0"]


def _style_name(resource):
    return _punc.sub("_", f"{resource.store.workspace.name}:{resource.name}")


def extract_name_from_sld(gs_catalog, sld, sld_file=None):
    try:
        if sld:
            if isfile(sld):
                with open(sld, "rb") as sld_file:
                    sld = sld_file.read()
            if isinstance(sld, str):
                sld = sld.encode("utf-8")
            dom = etree.XML(sld, parser=etree.XMLParser(resolve_entities=False))
        elif sld_file and isfile(sld_file):
            with open(sld_file, "rb") as sld_file:
                sld = sld_file.read()
            if isinstance(sld, str):
                sld = sld.encode("utf-8")
            dom = dlxml.parse(sld)
    except Exception:
        logger.exception("The uploaded SLD file is not valid XML")
        raise Exception("The uploaded SLD file is not valid XML")

    named_dataset = dom.findall("{http://www.opengis.net/sld}NamedLayer")
    user_dataset = dom.findall("{http://www.opengis.net/sld}UserLayer")

    el = None
    if named_dataset and len(named_dataset) > 0:
        user_style = named_dataset[0].findall("{http://www.opengis.net/sld}UserStyle")
        if user_style and len(user_style) > 0:
            el = user_style[0].findall("{http://www.opengis.net/sld}Name")
            if len(el) == 0:
                el = user_style[0].findall("{http://www.opengis.net/se}Name")

        if len(el) == 0:
            el = named_dataset[0].findall("{http://www.opengis.net/sld}Name")
        if len(el) == 0:
            el = named_dataset[0].findall("{http://www.opengis.net/se}Name")

    if not el or len(el) == 0:
        if user_dataset and len(user_dataset) > 0:
            user_style = user_dataset[0].findall("{http://www.opengis.net/sld}UserStyle")
            if user_style and len(user_style) > 0:
                el = user_style[0].findall("{http://www.opengis.net/sld}Name")
                if len(el) == 0:
                    el = user_style[0].findall("{http://www.opengis.net/se}Name")

            if len(el) == 0:
                el = user_dataset[0].findall("{http://www.opengis.net/sld}Name")
            if len(el) == 0:
                el = user_dataset[0].findall("{http://www.opengis.net/se}Name")

    if not el or len(el) == 0:
        if sld_file:
            return splitext(basename(sld_file))[0]
        else:
            raise Exception("Please provide a name, unable to extract one from the SLD.")

    return el[0].text


def get_sld_for(gs_catalog, layer):
    name = None
    gs_dataset = None
    gs_style = None

    _default_style = None
    _max_retries, _tries = getattr(ogc_server_settings, "MAX_RETRIES", 2), 0
    try:
        gs_dataset = gs_catalog.get_layer(layer.name)
        if gs_dataset.default_style:
            gs_style = gs_dataset.default_style.sld_body
            set_dataset_style(layer, layer.alternate, gs_style)
        name = gs_dataset.default_style.name
        _default_style = gs_dataset.default_style
    except Exception as e:
        logger.debug(e)
        name = None

    while not name and _tries < _max_retries:
        try:
            gs_dataset = gs_catalog.get_layer(layer.name)
            if gs_dataset:
                if gs_dataset.default_style:
                    gs_style = gs_dataset.default_style.sld_body
                    set_dataset_style(layer, layer.alternate, gs_style)
                name = gs_dataset.default_style.name
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
    res = gs_dataset.resource if gs_dataset else None
    if res and res.resource_type == "featureType":
        res.fetch()
        ft = res.store.get_resources(name=res.name)
        ft.fetch()
        for attr in ft.dom.find("attributes"):
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
        return _style_templates[name] % dict(name=layer.name, fg=fg, bg=bg, mark=mark)
    else:
        return gs_style


def set_dataset_style(saved_dataset, title, sld, base_file=None):
    # Check SLD is valid
    try:
        if sld:
            if isfile(sld):
                with open(sld, "rb") as sld_file:
                    sld = sld_file.read()

            elif isinstance(sld, str):
                sld = sld.strip("b'\n")
                sld = re.sub(r"(\\r)|(\\n)", "", sld).encode("UTF-8")
            etree.XML(sld, parser=etree.XMLParser(resolve_entities=False))
        elif base_file and isfile(base_file):
            with open(base_file, "rb") as sld_file:
                sld = sld_file.read()
            dlxml.parse(base_file)
    except Exception:
        logger.exception("The uploaded SLD file is not valid XML")
        raise Exception("The uploaded SLD file is not valid XML")

    # Check Dataset's available styles
    match = None
    styles = list(saved_dataset.styles.all()) + [saved_dataset.default_style]
    for style in styles:
        if style and style.name == saved_dataset.name:
            match = style
            break
    layer = gs_catalog.get_layer(title)
    style = None
    if match is None:
        try:
            style = gs_catalog.get_style(saved_dataset.name, workspace=saved_dataset.workspace) or gs_catalog.get_style(
                saved_dataset.name
            )
            if not style:
                style = gs_catalog.create_style(
                    saved_dataset.name, sld, overwrite=False, raw=True, workspace=saved_dataset.workspace
                )
        except Exception as e:
            logger.exception(e)
    else:
        try:
            _sld_format = _extract_style_version_from_sld(sld)
            style = gs_catalog.create_style(
                saved_dataset.name,
                sld,
                overwrite=True,
                raw=True,
                style_format=_sld_format,
                workspace=saved_dataset.workspace,
            )
        except Exception as e:
            logger.exception(e)

    if layer and style:
        _old_styles = []
        _old_styles.append(gs_catalog.get_style(name=saved_dataset.name))
        _old_styles.append(gs_catalog.get_style(name=f"{saved_dataset.workspace}_{saved_dataset.name}"))
        if layer.default_style and layer.default_style.name:
            _old_styles.append(gs_catalog.get_style(name=layer.default_style.name))
            _old_styles.append(
                gs_catalog.get_style(name=layer.default_style.name, workspace=layer.default_style.workspace)
            )
        layer.default_style = style
        gs_catalog.save(layer)
        for _s in _old_styles:
            try:
                gs_catalog.delete(_s)
                Link.objects.filter(
                    resource=saved_dataset.resourcebase_ptr, name="Legend", url__contains=f"STYLE={_s.name}"
                ).delete()
            except Exception as e:
                logger.debug(e)
        set_styles(saved_dataset, gs_catalog)


def cascading_delete(dataset_name=None, catalog=None):
    if not dataset_name:
        return
    cat = catalog or gs_catalog
    resource = None
    workspace = None
    try:
        if dataset_name.find(":") != -1 and len(dataset_name.split(":")) == 2:
            workspace, name = dataset_name.split(":")
            ws = cat.get_workspace(workspace)
            store = None
            try:
                store = get_store(cat, name, workspace=ws)
            except FailedRequestError:
                if ogc_server_settings.DATASTORE:
                    try:
                        layers = Dataset.objects.filter(alternate=dataset_name)
                        for layer in layers:
                            store = get_store(cat, layer.store, workspace=ws)
                    except FailedRequestError:
                        logger.debug("the store was not found in geoserver")
                else:
                    logger.debug("the store was not found in geoserver")
            if ws is None or store is None:
                logger.debug("cascading delete was called on a layer where the workspace was not found")
            resource = cat.get_resource(name=name, store=store, workspace=workspace)
        else:
            resource = cat.get_resource(name=dataset_name)
    except OSError as e:
        if e.errno == errno.ECONNREFUSED:
            msg = (
                f'Could not connect to geoserver at "{ogc_server_settings.LOCATION}"'
                f'to save information for layer "{dataset_name}"'
            )
            logger.error(msg)
            return None
        else:
            raise e
    finally:
        # Let's reset the connections first
        cat._cache.clear()
        cat.reset()
        cat.reload()

    if resource is None:
        # If there is no associated resource,
        # this method can not delete anything.
        # Let's return and make a note in the log.
        logger.debug("cascading_delete was called with a non existent resource")
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
                    cat.delete(s, purge="true")
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
            pass

        if (
            store.resource_type == "dataStore"
            and "dbtype" in store.connection_parameters
            and store.connection_parameters["dbtype"] == "postgis"
        ):
            delete_from_postgis(resource_name, store)
        else:
            # AF: for the time being this one mitigates the issue #8671
            # until we find a suitable solution for the GeoTools ImageMosaic plugin
            # ref: https://github.com/geotools/geotools/blob/main/modules/plugin/imagemosaic/src/main/java/org/geotools/gce/imagemosaic/catalog/AbstractGTDataStoreGranuleCatalog.java#L753
            if store.resource_type == "coverageStore" and store.type != "ImageMosaic":
                try:
                    logger.debug(f" - Going to purge the {store.resource_type} : {store.href}")
                    cat.reset()  # this resets the coverage readers and unlocks the files
                    cat.delete(store, purge="all", recurse=True)
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


def delete_from_postgis(dataset_name, store):
    """
    Delete a table from PostGIS (because Geoserver won't do it yet);
    to be used after deleting a layer from the system.
    """
    import psycopg2

    # we will assume that store/database may change (when using shard for example)
    # but user and password are the ones from settings (DATASTORE_URL)
    db = ogc_server_settings.datastore_db
    db_name = store.connection_parameters["database"]
    user = db["USER"]
    password = db["PASSWORD"]
    host = store.connection_parameters["host"]
    port = store.connection_parameters["port"]
    conn = None
    try:
        conn = psycopg2.connect(dbname=db_name, user=user, host=host, port=port, password=password)
        cur = conn.cursor()
        cur.execute(f"SELECT DropGeometryTable ('{dataset_name}')")
        conn.commit()
    except Exception as e:
        logger.error("Error deleting PostGIS table %s:%s", dataset_name, str(e))
    finally:
        try:
            if conn:
                conn.close()
        except Exception as e:
            logger.error("Error closing PostGIS conn %s:%s", dataset_name, str(e))


def gs_slurp(
    ignore_errors=False,
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
    execute_signals=False,
):
    """Configure the layers available in GeoServer in GeoNode.
    It returns a list of dictionaries with the name of the layer,
    the result of the operation and the errors and traceback if it failed.
    """
    from geonode.resource.manager import resource_manager

    if console is None:
        console = open(os.devnull, "w")

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
            resources_for_delete_compare = [k for k in resources_for_delete_compare if k.enabled in {"true", True}]
            if skip_unadvertised:
                resources_for_delete_compare = [
                    k for k in resources_for_delete_compare if k.advertised in {"true", True}
                ]
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
    dataset_names = Dataset.objects.values_list("alternate", flat=True)
    if skip_geonode_registered:
        try:
            resources = [k for k in resources if f"{k.workspace.name}:{k.name}" not in dataset_names]
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
        "stats": {
            "failed": 0,
            "updated": 0,
            "created": 0,
            "deleted": 0,
        },
        "layers": [],
        "deleted_datasets": [],
    }
    start = datetime.datetime.now(timezone.get_current_timezone())
    for i, resource in enumerate(resources):
        name = resource.name
        the_store = resource.store
        workspace = the_store.workspace
        layer = None
        try:
            created = False
            layer = Dataset.objects.filter(name=name, workspace=workspace.name).first()
            if not layer:
                layer = resource_manager.create(
                    str(uuid.uuid4()),
                    resource_type=Dataset,
                    defaults=dict(
                        name=name,
                        workspace=workspace.name,
                        store=the_store.name,
                        subtype=get_dataset_storetype(the_store.resource_type),
                        alternate=f"{workspace.name}:{resource.name}",
                        title=resource.title or _("No title provided"),
                        abstract=resource.abstract or _("No abstract provided"),
                        owner=owner,
                    ),
                )
                created = True
            # Hide the resource until finished
            layer.set_processing_state("RUNNING")
            bbox = resource.native_bbox
            ll_bbox = resource.latlon_bbox
            try:
                layer.set_bbox_polygon([bbox[0], bbox[2], bbox[1], bbox[3]], resource.projection)
            except GeoNodeException as e:
                if not ll_bbox:
                    raise
                else:
                    logger.exception(e)
                    layer.srid = "EPSG:4326"
            layer.set_ll_bbox_polygon([ll_bbox[0], ll_bbox[2], ll_bbox[1], ll_bbox[3]])

            # sync permissions in GeoFence
            perm_spec = json.loads(_perms_info_json(layer))
            resource_manager.set_permissions(layer.uuid, permissions=perm_spec)

            # recalculate the layer statistics
            set_attributes_from_geoserver(layer, overwrite=True)

            # in some cases we need to explicitily save the resource to execute the signals
            # (for sure when running updatelayers)
            resource_manager.update(layer.uuid, instance=layer, notify=execute_signals)

            # Creating the Thumbnail
            resource_manager.set_thumbnail(layer.uuid, overwrite=True, check_bbox=False)

        except Exception as e:
            # Hide the resource until finished
            if layer:
                layer.set_processing_state("FAILED")
            if ignore_errors:
                status = "failed"
                exception_type, error, traceback = sys.exc_info()
            else:
                if verbosity > 0:
                    msg = "Stopping process because --ignore-errors was not set and an error was found."
                    print(msg, file=sys.stderr)
                raise Exception(f"Failed to process {resource.name}") from e
        if layer is None:
            if ignore_errors:
                status = "failed"
                exception_type, error, traceback = sys.exc_info()
            else:
                if verbosity > 0:
                    msg = "Stopping process because --ignore-errors was not set and an error was found."
                    print(msg, file=sys.stderr)
                raise Exception(f"Failed to process {resource.name}")
        else:
            if created:
                if not permissions:
                    layer.set_default_permissions()
                else:
                    layer.set_permissions(permissions)

                status = "created"
                output["stats"]["created"] += 1
            else:
                status = "updated"
                output["stats"]["updated"] += 1

        msg = f"[{status}] Dataset {name} ({(i + 1)}/{number})"
        info = {"name": name, "status": status}
        if status == "failed":
            output["stats"]["failed"] += 1
            info["traceback"] = traceback
            info["exception_type"] = exception_type
            info["error"] = error
        output["layers"].append(info)
        if verbosity > 0:
            print(msg, file=console)

    if remove_deleted:
        q = Dataset.objects.filter()
        if workspace_for_delete_compare is not None:
            if isinstance(workspace_for_delete_compare, Workspace):
                q = q.filter(workspace__exact=workspace_for_delete_compare.name)
            else:
                q = q.filter(workspace__exact=workspace_for_delete_compare)
        if store is not None:
            if isinstance(store, CoverageStore) or isinstance(store, DataStore):
                q = q.filter(store__exact=store.name)
            else:
                q = q.filter(store__exact=store)
        logger.debug("Executing 'remove_deleted' logic")
        logger.debug("GeoNode Layers Found:")

        # compare the list of GeoNode layers obtained via query/filter with valid resources found in GeoServer
        # filtered per options passed to updatelayers: --workspace, --store, --skip-unadvertised
        # add any layers not found in GeoServer to deleted_datasets (must match
        # workspace and store as well):
        deleted_datasets = []
        for layer in q:
            logger.debug(
                "GeoNode Dataset info: name: %s, workspace: %s, store: %s", layer.name, layer.workspace, layer.store
            )
            dataset_found_in_geoserver = False
            for resource in resources_for_delete_compare:
                # if layer.name matches a GeoServer resource, check also that
                # workspace and store match, mark valid:
                if layer.name == resource.name:
                    if layer.workspace == resource.workspace.name and layer.store == resource.store.name:
                        logger.debug(
                            "Matches GeoServer layer: name: %s, workspace: %s, store: %s",
                            resource.name,
                            resource.workspace.name,
                            resource.store.name,
                        )
                        dataset_found_in_geoserver = True
            if not dataset_found_in_geoserver:
                logger.debug("----- Dataset %s not matched, marked for deletion ---------------", layer.name)
                deleted_datasets.append(layer)

        number_deleted = len(deleted_datasets)
        if verbosity > 0:
            msg = (
                "\nFound %d layers to delete, starting processing" % number_deleted
                if number_deleted > 0
                else "\nFound %d layers to delete" % number_deleted
            )
            print(msg, file=console)

        for i, layer in enumerate(deleted_datasets):
            logger.debug(
                "GeoNode Dataset to delete: name: %s, workspace: %s, store: %s",
                layer.name,
                layer.workspace,
                layer.store,
            )
            try:
                # delete ratings, and taggit tags:
                layer.keywords.clear()

                layer.delete()
                output["stats"]["deleted"] += 1
                status = "delete_succeeded"
            except Exception:
                status = "delete_failed"

            msg = f"[{status}] Dataset {layer.name} ({(i + 1)}/{number_deleted})"
            info = {"name": layer.name, "status": status}
            if status == "delete_failed":
                exception_type, error, traceback = sys.exc_info()
                info["traceback"] = traceback
                info["exception_type"] = exception_type
                info["error"] = error
            output["deleted_datasets"].append(info)
            if verbosity > 0:
                print(msg, file=console)

    finish = datetime.datetime.now(timezone.get_current_timezone())
    td = finish - start
    output["stats"]["duration_sec"] = td.microseconds / 1000000 + td.seconds + td.days * 24 * 3600
    return output


def get_stores(store_type=None):
    cat = gs_catalog
    stores = cat.get_stores()
    store_list = []
    for store in stores:
        store.fetch()
        stype = store.dom.find("type").text.lower()
        if store_type and store_type.lower() == stype:
            store_list.append({"name": store.name, "type": stype})
        elif store_type is None:
            store_list.append({"name": store.name, "type": stype})
    return store_list


def set_attributes(layer, attribute_map, overwrite=False, attribute_stats=None):
    """*layer*: a geonode.layers.models.Dataset instance
    *attribute_map*: a list of 2-lists specifying attribute names and types,
        example: [ ['id', 'Integer'], ... ]
    *overwrite*: replace existing attributes with new values if name/type matches.
    *attribute_stats*: dictionary of return values from get_attribute_statistics(),
        of the form to get values by referencing attribute_stats[<dataset_name>][<field_name>].
    """
    # we need 3 more items; description, attribute_label, and display_order
    attribute_map_dict = {
        "field": 0,
        "ftype": 1,
        "description": 2,
        "label": 3,
        "display_order": 4,
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
                attribute[attribute_map_dict["description"]] = la.description
                attribute[attribute_map_dict["label"]] = la.attribute_label
                attribute[attribute_map_dict["display_order"]] = la.display_order
        if overwrite or not lafound:
            logger.debug("Going to delete [%s] for [%s]", la.attribute, layer.name)
            la.delete()

    # Add new layer attributes if they doesn't exist already
    if attribute_map:
        iter = len(Attribute.objects.filter(dataset=layer)) + 1
        for attribute in attribute_map:
            field, ftype, description, label, display_order = attribute
            if field:
                _gs_attrs = Attribute.objects.filter(dataset=layer, attribute=field)
                if _gs_attrs.count() == 1:
                    la = _gs_attrs.get()
                else:
                    if _gs_attrs.exists():
                        _gs_attrs.delete()
                    la = Attribute.objects.create(dataset=layer, attribute=field)
                    la.visible = ftype.find("gml:") != 0
                    la.attribute_type = ftype
                    la.description = description
                    la.attribute_label = label
                    la.display_order = iter
                    iter += 1
                if not attribute_stats or layer.name not in attribute_stats or field not in attribute_stats[layer.name]:
                    result = None
                else:
                    result = attribute_stats[layer.name][field]
                if result:
                    logger.debug("Generating layer attribute statistics")
                    la.count = result["Count"]
                    la.min = result["Min"]
                    la.max = result["Max"]
                    la.average = result["Average"]
                    la.median = result["Median"]
                    la.stddev = result["StandardDeviation"]
                    la.sum = result["Sum"]
                    la.unique_values = result["unique_values"]
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
    if getattr(layer, "remote_service") and layer.remote_service:
        server_url = layer.remote_service.service_url
        if layer.remote_service.operations.get("GetCapabilities", None) and layer.remote_service.operations.get(
            "GetCapabilities"
        ).get("methods"):
            for _method in layer.remote_service.operations.get("GetCapabilities").get("methods"):
                if _method.get("type", "").upper() == "GET":
                    server_url = _method.get("url", server_url)
                    break
    else:
        server_url = ogc_server_settings.LOCATION
    if layer.subtype in ["tileStore", "remote"] and layer.remote_service.ptype == "gxp_arcrestsource":
        logger.info(f"Getting info for {layer.subtype} '{layer.alternate or layer.typename}'")
        dft_url = f"{server_url}{(layer.alternate or layer.typename)}?f=json"
        try:
            # The code below will fail if http_client cannot be imported
            req, body = http_client.get(dft_url, user=_user)
            body = json.loads(body)
            attribute_map = [
                [n["name"], _esri_types[n["type"]]] for n in body["fields"] if n.get("name") and n.get("type")
            ]
        except Exception:
            logger.warning(
                f"Error while retrieving info for {layer.subtype} '{layer.alternate or layer.typename}'", exc_info=True
            )
            attribute_map = []
    elif layer.subtype in {"vector", "tileStore", "remote", "wmsStore", "vector_time"}:
        typename = layer.alternate if layer.alternate else layer.typename
        logger.info(f"Getting WFS info for {layer.subtype} '{typename}'")
        dft_url_path = re.sub(r"\/wms\/?$", "/", server_url)
        dft_query = urlencode(
            {"service": "wfs", "version": "1.0.0", "request": "DescribeFeatureType", "typename": typename}
        )
        dft_url = urljoin(dft_url_path, f"ows?{dft_query}")
        logger.debug(f"WFS URL is  {dft_url}")
        try:
            # The code below will fail if http_client cannot be imported or WFS not supported
            doc = _get_xml(dft_url)
            xsd = "{http://www.w3.org/2001/XMLSchema}"
            path = f".//{xsd}extension/{xsd}sequence/{xsd}element"
            attribute_map = [
                [n.attrib["name"], n.attrib["type"]]
                for n in doc.findall(path)
                if n.attrib.get("name") and n.attrib.get("type")
            ]
        except Exception:
            logger.warning(
                f"Error while retrieving WFS info for {layer.subtype} '{typename}'... will try WMS", exc_info=True
            )
            attribute_map = []
            # Try WMS instead
            dft_url = (
                server_url
                + "?"
                + urlencode(
                    {
                        "service": "wms",
                        "version": "1.0.0",
                        "request": "GetFeatureInfo",
                        "bbox": ",".join([str(x) for x in layer.bbox]),
                        "LAYERS": layer.alternate,
                        "QUERY_LAYERS": typename,
                        "feature_count": 1,
                        "width": 1,
                        "height": 1,
                        "srs": "EPSG:4326",
                        "info_format": "text/html",
                        "x": 1,
                        "y": 1,
                    }
                )
            )
            try:
                logger.info(f"Getting WMS info for {layer.subtype} '{layer.alternate or layer.typename}'")
                logger.debug(f"WMS URL is {dft_url}")
                body = _get_from_catalog(dft_url)
                soup = BeautifulSoup(body, features="lxml")
                for field in soup.findAll("th"):
                    if field.string is None:
                        field_name = field.contents[0].string
                    else:
                        field_name = field.string
                    attribute_map.append([field_name, "xsd:string"])
            except Exception:
                logger.warning(f"Error while retrieving WMS info for {layer.subtype} '{typename}'", exc_info=True)
                attribute_map = []
    elif layer.subtype in ["raster"]:
        typename = layer.alternate if layer.alternate else layer.typename
        logger.info(f"Getting WCS info for {layer.subtype} '{typename}'")
        dc_url = f"{server_url}wcs?{urlencode({'service': 'wcs', 'version': '1.1.0', 'request': 'DescribeCoverage', 'identifiers': typename})}"
        try:
            doc = _get_xml(dc_url)
            wcs = "{http://www.opengis.net/wcs/1.1.1}"
            path = f".//{wcs}Axis/{wcs}AvailableKeys/{wcs}Key"
            attribute_map = [[n.text, "raster"] for n in doc.findall(path)]
        except Exception:
            logger.warning(f"Error while retrieving WCS info for {layer.subtype} '{typename}'", exc_info=True)
            attribute_map = []
    # Get attribute statistics & package for call to really_set_attributes()
    attribute_stats = defaultdict(dict)
    # Add new layer attributes if they don't already exist
    for attribute in attribute_map:
        field, ftype = attribute
        if field is not None:
            if Attribute.objects.filter(dataset=layer, attribute=field).exists():
                continue
            elif is_dataset_attribute_aggregable(layer.subtype, field, ftype):
                logger.debug("Generating layer attribute statistics")
                result = get_attribute_statistics(layer.alternate or layer.typename, field)
            else:
                result = None
            attribute_stats[layer.name][field] = result
    logger.info(f"Found {len(attribute_map)} attributes for {layer.subtype}")
    set_attributes(layer, attribute_map, overwrite=overwrite, attribute_stats=attribute_stats)


def get_dataset(layer, gs_catalog: Catalog):
    gs_catalog.reset()
    gs_dataset = None
    try:
        gs_dataset = gs_catalog.get_layer(layer.name)
    except Exception:
        tb = traceback.format_exc()
        logger.exception(tb)

    if not gs_dataset:
        try:
            gs_dataset = gs_catalog.get_layer(layer.alternate or layer.typename)
        except Exception:
            tb = traceback.format_exc()
            logger.error(tb)
            logger.exception("No GeoServer Dataset found!")
    return gs_dataset


def clean_styles(layer, gs_catalog: Catalog):
    try:
        # Cleanup Styles without a Workspace
        style = None
        gs_catalog.reset()
        gs_dataset = get_dataset(layer, gs_catalog)
        if gs_dataset is not None:
            logger.debug(f'clean_styles: Retrieving style "{gs_dataset.default_style.name}" for cleanup')
            style = gs_catalog.get_style(name=gs_dataset.default_style.name, workspace=None, recursive=True)
        if style:
            gs_catalog.delete(style, purge=True, recurse=False)
            logger.debug(f"clean_styles: Style removed: {gs_dataset.default_style.name}")
        else:
            logger.debug(f"clean_styles: Style does not exist: {gs_dataset.default_style.name}")
    except Exception as e:
        logger.warning(f"Could not clean style for layer {layer.name}", exc_info=e)
        logger.debug(f"Could not clean style for layer {layer.name} - STACK INFO", stack_info=True)


def set_styles(layer, gs_catalog: Catalog):
    style_set = []
    gs_dataset = get_dataset(layer, gs_catalog)
    if gs_dataset:
        default_style = gs_dataset.get_full_default_style()
        if default_style:
            # make sure we are not using a default SLD (which won't be editable)
            layer.default_style, _gs_default_style = save_style(default_style, layer)
            try:
                if (
                    default_style.name != _gs_default_style.name
                    or default_style.workspace != _gs_default_style.workspace
                ):
                    logger.debug(f'set_style: Setting default style "{_gs_default_style.name}" for layer "{layer.name}')

                    gs_dataset.default_style = _gs_default_style
                    gs_catalog.save(gs_dataset)
                    if default_style.name not in DEFAULT_STYLE_NAME:
                        logger.debug(
                            f'set_style: Retrieving no-workspace default style "{default_style.name}" for deletion'
                        )
                        style_to_delete = gs_catalog.get_style(name=default_style.name, workspace=None, recursive=True)
                        if style_to_delete:
                            gs_catalog.delete(style_to_delete, purge=True, recurse=False)
                            logger.debug(f"set_style: No-ws default style deleted: {default_style.name}")
                        else:
                            logger.debug(f"set_style: No-ws default style does not exist: {default_style.name}")
            except Exception as e:
                logger.error(
                    f'Error setting default style "{_gs_default_style.name}" for layer "{layer.name}', exc_info=e
                )

            style_set.append(layer.default_style)

        try:
            if gs_dataset.styles:
                alt_styles = gs_dataset.styles
                for alt_style in alt_styles:
                    if (
                        alt_style
                        and alt_style.name
                        and alt_style.name != layer.default_style.name
                        and alt_style.workspace != layer.default_style.workspace
                    ):
                        _s, _ = save_style(alt_style, layer)
                        style_set.append(_s)
        except Exception as e:
            logger.exception(e)

    if style_set:
        # Remove duplicates
        style_set = list(dict.fromkeys(style_set))
        layer.styles.set(style_set)

    clean_styles(layer, gs_catalog)

    # Update default style to database
    to_update = {"default_style": layer.default_style}

    Dataset.objects.filter(id=layer.id).update(**to_update)
    layer.refresh_from_db()

    # Legend links
    logger.debug(f" -- Resource Links[Legend link] for layer {layer.name}...")
    try:
        from geonode.base.models import Link

        dataset_legends = Link.objects.filter(resource=layer.resourcebase_ptr, name="Legend")
        for style in set(
            list(layer.styles.all())
            + [
                layer.default_style,
            ]
        ):
            if style:
                style_name = os.path.basename(urlparse(style.sld_url).path).split(".")[0]
                legend_url = get_legend_url(layer, style_name)
                if dataset_legends.filter(resource=layer.resourcebase_ptr, name="Legend", url=legend_url).count() < 2:
                    Link.objects.update_or_create(
                        resource=layer.resourcebase_ptr,
                        name="Legend",
                        url=legend_url,
                        defaults=dict(
                            extension="png",
                            url=legend_url,
                            mime="image/png",
                            link_type="image",
                        ),
                    )
        logger.debug(" -- Resource Links[Legend link]...done!")
    except Exception as e:
        logger.debug(f" -- Resource Links[Legend link]...error: {e}")

    try:
        from .security import set_geowebcache_invalidate_cache

        set_geowebcache_invalidate_cache(layer.alternate or layer.typename, cat=gs_catalog)
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)


def save_style(gs_style, layer):
    style_name = os.path.basename(urlparse(gs_style.body_href).path).split(".")[0]
    sld_name = copy.copy(gs_style.name)
    sld_body = copy.copy(gs_style.sld_body)
    _gs_style = None
    if not gs_style.workspace:
        logger.debug(f'save_style: Copying style "{sld_name}" to "{layer.workspace}:{layer.name}')
        _gs_style = gs_catalog.create_style(layer.name, sld_body, raw=True, overwrite=True, workspace=layer.workspace)
    else:
        logger.debug(
            f'save_style: Retrieving style "{layer.workspace}:{sld_name}" for layer "{layer.workspace}:{layer.name}'
        )
        _gs_style = gs_catalog.get_style(name=sld_name, workspace=layer.workspace)

    style = None
    try:
        style, _ = Style.objects.get_or_create(name=style_name)
        style.workspace = _gs_style.workspace
        style.sld_title = _gs_style.sld_title if _gs_style.style_format != "css" and _gs_style.sld_title else sld_name
        style.sld_body = _gs_style.sld_body
        style.sld_url = _gs_style.body_href
        style.save()
    except Exception as e:
        tb = traceback.format_exc()
        logger.debug(tb)
        raise e
    return (style, _gs_style)


def is_dataset_attribute_aggregable(store_type, field_name, field_type):
    """
    Decipher whether layer attribute is suitable for statistical derivation
    """

    # must be vector layer
    if store_type != "dataStore":
        return False
    # must be a numeric data type
    if field_type not in LAYER_ATTRIBUTE_NUMERIC_DATA_TYPES:
        return False
    # must not be an identifier type field
    if field_name.lower() in {"id", "identifier"}:
        return False

    return True


def get_attribute_statistics(dataset_name, field):
    """
    Generate statistics (range, mean, median, standard deviation, unique values)
    for layer attribute
    """

    logger.debug("Deriving aggregate statistics for attribute %s", field)

    if not ogc_server_settings.WPS_ENABLED:
        return None
    try:
        return wps_execute_dataset_attribute_statistics(dataset_name, field)
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)
        logger.exception("Error generating layer aggregate statistics")


def get_wcs_record(instance, retry=True):
    wcs = WebCoverageService(f"{ogc_server_settings.LOCATION}wcs", "1.0.0")
    key = f"{instance.workspace}:{instance.name}"
    logger.debug(wcs.contents)
    if key in wcs.contents:
        return wcs.contents[key]
    else:
        msg = f"Dataset '{key}' was not found in WCS service at {ogc_server_settings.public_url}."
        if retry:
            logger.debug(f"{msg} Waiting a couple of seconds before trying again.")
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
    return [(int(h) - int(l) + 1) for h, l in zip(grid.highlimits, grid.lowlimits)]


GEOSERVER_LAYER_TYPES = {
    "vector": FeatureType.resource_type,
    "raster": Coverage.resource_type,
}


def cleanup(name, uuid):
    """Deletes GeoServer and Catalogue records for a given name.
    Useful to clean the mess when something goes terribly wrong.
    It also verifies if the Django record existed, in which case
    it performs no action.
    """
    try:
        Dataset.objects.get(name=name)
    except Dataset.DoesNotExist:
        pass
    else:
        msg = f"Not doing any cleanup because the layer {name} exists in the Django db."
        raise GeoNodeException(msg)

    cat = gs_catalog
    gs_store = None
    gs_dataset = None
    gs_resource = None
    # FIXME: Could this lead to someone deleting for example a postgis db
    # with the same name of the uploaded file?.
    try:
        gs_store = cat.get_store(name)
        if gs_store is not None:
            gs_dataset = cat.get_layer(name)
            if gs_dataset is not None:
                gs_resource = gs_dataset.resource
        else:
            gs_dataset = None
            gs_resource = None
    except FailedRequestError as e:
        msg = ("Couldn't connect to GeoServer while cleaning up layer " "[%s] !!", str(e))
        logger.warning(msg)

    if gs_dataset is not None:
        try:
            cat.delete(gs_dataset)
        except Exception:
            logger.warning("Couldn't delete GeoServer layer during cleanup()")
    if gs_resource is not None:
        try:
            cat.delete(gs_resource)
        except Exception:
            msg = "Couldn't delete GeoServer resource during cleanup()"
            logger.warning(msg)
    if gs_store is not None:
        try:
            cat.delete(gs_store)
        except Exception:
            logger.warning("Couldn't delete GeoServer store during cleanup()")

    logger.warning("Deleting dangling Catalogue record for [%s] " "(no Django record to match)", name)

    if "geonode.catalogue" in settings.INSTALLED_APPS:
        from geonode.catalogue import get_catalogue

        catalogue = get_catalogue()
        catalogue.remove_record(uuid)
        logger.warning("Finished cleanup after failed Catalogue/Django " "import for layer: %s", name)


def create_geoserver_db_featurestore(
    store_type=None,
    store_name=None,
    author_name="admin",
    author_email="admin@geonode.org",
    charset="UTF-8",
    workspace=None,
):
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
        logger.debug(f"Creating target datastore {dsname}")
        ds = cat.create_datastore(dsname, workspace=workspace)
        db = ogc_server_settings.datastore_db
        db_engine = "postgis" if "postgis" in db["ENGINE"] else db["ENGINE"]
        ds.connection_parameters.update(
            {
                "Evictor run periodicity": 300,
                "Estimated extends": "true",
                "fetch size": 100000,
                "encode functions": "false",
                "Expose primary keys": "true",
                "validate connections": "true",
                "Support on the fly geometry simplification": "false",
                "Connection timeout": 10,
                "create database": "false",
                "Batch insert size": 30,
                "preparedStatements": "true",
                "min connections": 10,
                "max connections": 100,
                "Evictor tests per run": 3,
                "Max connection idle time": 300,
                "Loose bbox": "true",
                "Test while idle": "true",
                "host": db["HOST"],
                "port": db["PORT"] if isinstance(db["PORT"], str) else str(db["PORT"]) or "5432",
                "database": db["NAME"],
                "user": db["USER"],
                "passwd": db["PASSWORD"],
                "dbtype": db_engine,
            }
        )

    if ds_exists:
        ds.save_method = "PUT"
    else:
        logger.debug("Updating target datastore % s" % dsname)
        try:
            cat.save(ds)
        except FailedRequestError as e:
            if "already exists in workspace" not in e.args[0]:
                raise e
            logger.warning("The store was already present in the workspace selected")

    logger.debug("Reloading target datastore % s" % dsname)
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
    dsname = db["NAME"]
    ds = create_geoserver_db_featurestore(store_name=dsname, workspace=workspace)

    try:
        cat.add_data_to_store(ds, name, data, overwrite=overwrite, workspace=workspace, charset=charset)
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
            store = cat.get_xml(f"{workspace.datastore_url[:-4]}/{name}.xml")
        except FailedRequestError:
            try:
                store = cat.get_xml(f"{workspace.coveragestore_url[:-4]}/{name}.xml")
            except FailedRequestError:
                try:
                    store = cat.get_xml(f"{workspace.wmsstore_url[:-4]}/{name}.xml")
                except FailedRequestError:
                    raise FailedRequestError(f"No store found named: {name}")
        if store:
            if store.tag == "dataStore":
                store = datastore_from_index(cat, workspace, store)
            elif store.tag == "coverageStore":
                store = coveragestore_from_index(cat, workspace, store)
            elif store.tag == "wmsStore":
                store = wmsstore_from_index(cat, workspace, store)
            return store
        else:
            raise FailedRequestError(f"No store found named: {name}")
    else:
        raise FailedRequestError(f"No store found named: {name}")


def fetch_gs_resource(instance, values, tries):
    try:
        gs_resource = gs_catalog.get_resource(name=instance.name, store=instance.store, workspace=instance.workspace)
    except Exception:
        try:
            gs_resource = gs_catalog.get_resource(
                name=instance.alternate, store=instance.store, workspace=instance.workspace
            )
        except Exception:
            try:
                gs_resource = gs_catalog.get_resource(name=instance.alternate or instance.typename)
            except Exception:
                gs_resource = None
    if gs_resource:
        if values:
            gs_resource.title = values.get("title", "")
            gs_resource.abstract = values.get("abstract", "")
        else:
            values = {}

        _subtype = gs_resource.store.resource_type
        if (
            getattr(gs_resource, "metadata", None)
            and gs_resource.metadata.get("time", False)
            and gs_resource.metadata.get("time").enabled
        ):
            _subtype = "vectorTimeSeries"

        values.update(
            dict(
                store=gs_resource.store.name,
                subtype=_subtype,
                alternate=f"{gs_resource.store.workspace.name}:{gs_resource.name}",
                title=gs_resource.title or gs_resource.store.name,
                abstract=gs_resource.abstract or "",
                owner=instance.owner,
            )
        )
    else:
        msg = f"There isn't a geoserver resource for this layer: {instance.name}"
        logger.debug(msg)
        gs_resource = None
    return (values, gs_resource)


def wps_execute_dataset_attribute_statistics(dataset_name, field):
    """Derive aggregate statistics from WPS endpoint"""

    # generate statistics using WPS
    url = urljoin(ogc_server_settings.LOCATION, "ows")

    request = render_to_string("layers/wps_execute_gs_aggregate.xml", {"dataset_name": dataset_name, "field": field})
    u = urlsplit(url)

    headers = {
        "User-Agent": "OWSLib (https://geopython.github.io/OWSLib)",
        "Content-type": "text/xml",
        "Accept": "text/xml",
        "Accept-Language": "en-US",
        "Accept-Encoding": "gzip,deflate",
        "Host": u.netloc,
    }

    response, content = http_client.request(
        url, method="POST", data=request, headers=headers, user=_user, timeout=5, retries=1
    )

    exml = dlxml.fromstring(content.encode())

    result = {}

    for f in ["Min", "Max", "Average", "Median", "StandardDeviation", "Sum"]:
        fr = exml.find(f)
        if fr is not None:
            result[f] = fr.text
        else:
            result[f] = "NA"

    count = exml.find("Count")
    if count is not None:
        result["Count"] = int(count.text)
    else:
        result["Count"] = 0

    result["unique_values"] = "NA"

    return result


def _stylefilterparams_geowebcache_dataset(dataset_name):
    headers = {"Content-Type": "text/xml"}
    url = f"{ogc_server_settings.LOCATION}gwc/rest/layers/{dataset_name}.xml"

    # read GWC configuration
    req, content = http_client.get(url, headers=headers, user=_user)
    if req.status_code != 200:
        logger.error(f"Error {req.status_code} reading Style Filter Params GeoWebCache at {url}")
        return

    # check/write GWC filter parameters
    body = None
    tree = dlxml.fromstring(_)
    param_filters = tree.findall("parameterFilters")
    if param_filters and len(param_filters) > 0:
        if not param_filters[0].findall("styleParameterFilter"):
            style_filters_xml = "<styleParameterFilter><key>STYLES</key>\
                <defaultValue></defaultValue></styleParameterFilter>"
            style_filters_elem = dlxml.fromstring(style_filters_xml)
            param_filters[0].append(style_filters_elem)
            body = ET.tostring(tree)
    if body:
        req, content = http_client.post(url, data=body, headers=headers, user=_user)
        if req.status_code != 200:
            logger.error(f"Error {req.status_code} writing Style Filter Params GeoWebCache at {url}")


def _invalidate_geowebcache_dataset(dataset_name, url=None):
    # http.add_credentials(username, password)
    headers = {
        "Content-Type": "text/xml",
    }
    body = f"""
        <truncateLayer><layerName>{dataset_name}</layerName></truncateLayer>
        """.strip()
    if not url:
        url = f"{ogc_server_settings.LOCATION}gwc/rest/masstruncate"
    req, content = http_client.post(url, data=body, headers=headers, user=_user)

    if req.status_code != 200:
        logger.debug(f"Error {req.status_code} invalidating GeoWebCache at {url}")


def style_update(request, url, workspace=None):
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
    affected_datasets = []
    if request.method in ("POST", "PUT", "DELETE"):  # we need to parse xml
        # Need to remove NSx from IE11
        if "HTTP_USER_AGENT" in request.META:
            if "Trident/7.0" in request.META["HTTP_USER_AGENT"] and "rv:11.0" in request.META["HTTP_USER_AGENT"]:
                txml = re.sub(r'xmlns:NS[0-9]=""', "", request.body)
                txml = re.sub(r"NS[0-9]:", "", txml)
                request._body = txml
        style_name = os.path.basename(request.path)
        sld_title = style_name
        sld_body = None
        sld_url = url
        dataset_name = None
        if "name" in request.GET:
            style_name = request.GET["name"]
            sld_body = request.body
        elif request.method == "DELETE":
            style_name = os.path.basename(request.path)
        else:
            sld_body = request.body
            gs_style = gs_catalog.get_style(name=style_name) or gs_catalog.get_style(
                name=style_name, workspace=workspace
            )
            if gs_style:
                sld_title = gs_style.sld_title if gs_style.style_format != "css" and gs_style.sld_title else style_name
                sld_body = gs_style.sld_body
                sld_url = gs_style.body_href
            else:
                try:
                    tree = ET.ElementTree(dlxml.fromstring(request.body))
                    elm_nameddataset_name = tree.findall(".//{http://www.opengis.net/sld}Name")[0]
                    elm_user_style_name = tree.findall(".//{http://www.opengis.net/sld}Name")[1]
                    elm_user_style_title = tree.find(".//{http://www.opengis.net/sld}Title")
                    dataset_name = elm_nameddataset_name.text
                    if elm_user_style_title is None:
                        sld_title = elm_user_style_name.text
                    else:
                        sld_title = elm_user_style_title.text
                    sld_body = f'<?xml version="1.0" encoding="UTF-8"?>{request.body}'
                except Exception:
                    logger.warn("Could not recognize Style and Dataset name from Request!")

        # add style in GN and associate it to layer
        if request.method == "DELETE":
            if style_name:
                Style.objects.filter(name=style_name).delete()
        if request.method == "POST":
            style = None
            if style_name and not re.match(temp_style_name_regex, style_name):
                style, created = Style.objects.get_or_create(name=style_name)
                style.workspace = workspace
                style.sld_body = sld_body
                style.sld_url = sld_url
                style.sld_title = sld_title
                style.save()
            layer = None
            if dataset_name:
                try:
                    layer = Dataset.objects.get(name=dataset_name)
                except Exception:
                    try:
                        layer = Dataset.objects.get(alternate=dataset_name)
                    except Exception:
                        pass
            if layer:
                if style:
                    style.dataset_styles.add(layer)
                    style.save()
                affected_datasets.append(layer)
        elif request.method == "PUT":  # update style in GN
            if style_name and not re.match(temp_style_name_regex, style_name):
                style, created = Style.objects.get_or_create(name=style_name)
                style.workspace = workspace
                style.sld_body = sld_body
                style.sld_url = sld_url
                style.sld_title = sld_title
                style.save()
                for layer in style.dataset_styles.all():
                    affected_datasets.append(layer)

        # Invalidate GeoWebCache so it doesn't retain old style in tiles
        try:
            if dataset_name:
                _stylefilterparams_geowebcache_dataset(dataset_name)
                _invalidate_geowebcache_dataset(dataset_name)
        except Exception:
            pass
    return affected_datasets


def set_time_info(layer, attribute, end_attribute, presentation, precision_value, precision_step, enabled=True):
    """Configure the time dimension for a layer.

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
    """
    layer = gs_catalog.get_layer(layer.name)
    if layer is None:
        raise ValueError(f"no such layer: {layer.name}")
    resource = layer.resource if layer else None
    if not resource:
        resources = gs_catalog.get_resources(stores=[layer.name])
        if resources:
            resource = resources[0]

    resolution = None
    if precision_value and precision_step:
        resolution = f"{precision_value} {precision_step}"
    info = DimensionInfo(
        "time", enabled, presentation, resolution, "ISO8601", None, attribute=attribute, end_attribute=end_attribute
    )
    if resource and hasattr(resource, "metadata") and resource.metadata:
        metadata = dict(resource.metadata or {})
    else:
        metadata = dict({})
    metadata["time"] = info

    if resource and hasattr(resource, "metadata") and resource.metadata:
        resource.metadata = metadata
    else:
        setattr(resource, "metadata", metadata)

    if resource:
        gs_catalog.save(resource)


def get_time_info(layer):
    """Get the configured time dimension metadata for the layer as a dict.

    The keys of the dict will be those of the parameters of `set_time_info`.

    :returns: dict of values or None if not configured
    """
    layer = gs_catalog.get_layer(layer.name)
    if layer is None:
        raise ValueError(f"no such layer: {layer.name}")
    resource = layer.resource if layer else None
    if not resource:
        resources = gs_catalog.get_resources(stores=[layer.name])
        if resources:
            resource = resources[0]

    info = resource.metadata.get("time", None) if resource.metadata else None
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


ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)["default"]

_wms = None
_csw = None
_user, _password = ogc_server_settings.credentials

url = ogc_server_settings.rest
gs_catalog = Catalog(
    url, _user, _password, retries=ogc_server_settings.MAX_RETRIES, backoff_factor=ogc_server_settings.BACKOFF_FACTOR
)
gs_uploader = Client(url, _user, _password)


def _create_geofence_client():
    gf_rest_url = f'{url.rstrip("/")}/geofence/'
    client = GeoFenceClient(gf_rest_url, _user, _password)
    client.set_timeout(ogc_server_settings.GEOFENCE_TIMEOUT)
    return client


geofence = _create_geofence_client()
gf_utils = GeoFenceUtils(geofence)

_punc = re.compile(r"[\.:]")  # regex for punctuation that confuses restconfig
_foregrounds = ["#ffbbbb", "#bbffbb", "#bbbbff", "#ffffbb", "#bbffff", "#ffbbff"]
_backgrounds = ["#880000", "#008800", "#000088", "#888800", "#008888", "#880088"]
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
    "esriFieldTypeXML": "xsd:anyType",
}


def _dump_image_spec(request_body, image_spec):
    millis = int(round(time.time() * 1000))
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            _request_body_file_name = os.path.join(tmp_dir, f"request_body_{millis}.dump")
            _image_spec_file_name = os.path.join(tmp_dir, f"image_spec_{millis}.dump")
            with open(_request_body_file_name, "w") as _request_body_file:
                _request_body_file.write(f"{request_body}")
            copyfile(_request_body_file_name, os.path.join(tempfile.gettempdir(), f"request_body_{millis}.dump"))
            with open(_image_spec_file_name, "w") as _image_spec_file:
                _image_spec_file.write(f"{image_spec}")
            copyfile(_image_spec_file_name, os.path.join(tempfile.gettempdir(), f"image_spec_{millis}.dump"))
        return f"Dumping image_spec to: {os.path.join(tempfile.gettempdir(), f'image_spec_{millis}.dump')}"
    except Exception as e:
        logger.exception(e)
        return f"Unable to dump image_spec for request: {request_body}"


def mosaic_delete_first_granule(cat, layer):
    # - since GeoNode will uploade the first granule again through the Importer, we need to /
    #   delete the one created by the gs_config
    cat._cache.clear()
    store = cat.get_store(layer)
    coverages = cat.mosaic_coverages(store)

    granule_id = f"{layer}.1"

    cat.mosaic_delete_granule(coverages["coverages"]["coverage"][0]["name"], store, granule_id)


def set_time_dimension(
    cat,
    name,
    workspace,
    time_presentation,
    time_presentation_res,
    time_presentation_default_value,
    time_presentation_reference_value,
):
    # configure the layer time dimension as LIST
    presentation = time_presentation
    if not presentation:
        presentation = "LIST"

    resolution = None
    if time_presentation == "DISCRETE_INTERVAL":
        resolution = time_presentation_res

    strategy = None
    if time_presentation_default_value and not time_presentation_default_value == "":
        strategy = time_presentation_default_value

    timeInfo = DimensionInfo(
        "time",
        "true",
        presentation,
        resolution,
        "ISO8601",
        None,
        attribute="time",
        strategy=strategy,
        reference_value=time_presentation_reference_value,
    )

    layer = cat.get_layer(name)
    resource = layer.resource if layer else None
    if not resource:
        resources = cat.get_resources(stores=[name]) or cat.get_resources(stores=[name], workspaces=[workspace])
        if resources:
            resource = resources[0]

    if not resource:
        logger.exception(f"No resource could be found on GeoServer with name {name}")
        raise Exception(f"No resource could be found on GeoServer with name {name}")

    resource.metadata = {"time": timeInfo}
    cat.save(resource)


# main entry point to create a thumbnail - will use implementation
# defined in settings.THUMBNAIL_GENERATOR (see settings.py)
def create_gs_thumbnail(instance, overwrite=False, check_bbox=False):
    implementation = import_string(settings.THUMBNAIL_GENERATOR)
    return implementation(instance, overwrite, check_bbox)


def sync_instance_with_geoserver(instance_id, *args, **kwargs):
    """
    Synchronizes the Django Instance with GeoServer layers.
    """
    updatebbox = kwargs.get("updatebbox", True)
    updatemetadata = kwargs.get("updatemetadata", True)

    instance = None
    try:
        instance = Dataset.objects.get(id=instance_id)
    except Dataset.DoesNotExist:
        logger.error(f"Dataset id {instance_id} does not exist yet!")
        raise

    if isinstance(instance, ResourceBase):
        if hasattr(instance, "dataset"):
            instance = instance.dataset
        else:
            return instance

    try:
        instance.set_processing_state("RUNNING")
        if updatemetadata:
            # Save layer attributes
            logger.debug(f"... Refresh GeoServer attributes list for Dataset {instance.title}")
            try:
                set_attributes_from_geoserver(instance)
            except Exception as e:
                logger.warning(e)

        # Don't run this signal handler if it is a tile layer or a remote store (Service)
        #    Currently only gpkg files containing tiles will have this type & will be served via MapProxy.
        _is_remote_instance = hasattr(instance, "subtype") and getattr(instance, "subtype") in ["tileStore", "remote"]

        # Let's reset the connections first
        gs_catalog._cache.clear()
        gs_catalog.reset()

        gs_resource = None
        if not _is_remote_instance:
            values = {"title": instance.title, "abstract": instance.raw_abstract}
            _tries = 0
            _max_tries = getattr(ogc_server_settings, "MAX_RETRIES", 3)

            values, gs_resource = fetch_gs_resource(instance, values, _tries)
            while not gs_resource and _tries < _max_tries:
                values, gs_resource = fetch_gs_resource(instance, values, _tries)
                _tries += 1
                time.sleep(3)

            if gs_resource:
                logger.debug(f"Found geoserver resource for this dataset: {instance.name}")
                instance.gs_resource = gs_resource

                # Iterate over values from geoserver.
                for key in ["alternate", "store", "subtype"]:
                    # attr_name = key if 'typename' not in key else 'alternate'
                    # print attr_name
                    setattr(instance, key, get_dataset_storetype(values[key]))

                if updatemetadata:
                    # Get metadata links
                    metadata_links = []
                    for link in instance.link_set.metadata():
                        metadata_links.append((link.mime, link.name, link.url))
                    gs_resource.metadata_links = metadata_links

                    """
                    TODO: Attributions must be set on a Layer, not a Resource.
                    We should retrive gs_catalog.get_layer(name=instance.alternate), and obtain the resource from Layer.resource
                    but I'm not sure if at this stage the layer is ready. For the moment I disable this block.
                    default_poc = instance.get_first_contact_of_role(role="pointOfContact")
                    # Update Attribution link
                    if default_poc:
                        # gsconfig now utilizes an attribution dictionary
                        gs_resource.attribution = {
                            "title": str(instance.poc_csv),
                            "width": None,
                            "height": None,
                            "href": None,
                            "url": None,
                            "type": None,
                        }
                        profile = get_user_model().objects.get(username=default_poc.username)
                        site_url = (
                            settings.SITEURL.rstrip("/") if settings.SITEURL.startswith("http") else settings.SITEURL
                        )
                        gs_resource.attribution_link = site_url + profile.get_absolute_url()
                    """
                    try:
                        if settings.RESOURCE_PUBLISHING:
                            if instance.is_published != gs_resource.advertised:
                                gs_resource.advertised = "true"

                        if any(instance.keyword_list()):
                            keywords = gs_resource.keywords + instance.keyword_list()
                            gs_resource.keywords = list(set(keywords))

                        # gs_resource should only be called if
                        # ogc_server_settings.BACKEND_WRITE_ENABLED == True
                        if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
                            gs_catalog.save(gs_resource)
                    except Exception as e:
                        msg = f'Error while trying to save resource named {gs_resource} in GeoServer, try to use: "{e}"'
                        e.args = (msg,)
                        logger.warning(e)

                if updatebbox:
                    # store the resource to avoid another geoserver call in the post_save
                    """Get information from geoserver.
                    The attributes retrieved include:
                    * Bounding Box
                    * SRID
                    """
                    # This is usually done in Dataset.pre_save, however if the hooks
                    # are bypassed by custom create/updates we need to ensure the
                    # bbox is calculated properly.
                    srid = gs_resource.projection
                    bbox = gs_resource.native_bbox
                    ll_bbox = gs_resource.latlon_bbox
                    try:
                        instance.set_bbox_polygon([bbox[0], bbox[2], bbox[1], bbox[3]], srid)
                    except GeoNodeException as e:
                        if not ll_bbox:
                            raise
                        else:
                            logger.exception(e)
                            instance.srid = "EPSG:4326"
                            Dataset.objects.filter(id=instance.id).update(srid=instance.srid)
                    instance.set_ll_bbox_polygon([ll_bbox[0], ll_bbox[2], ll_bbox[1], ll_bbox[3]])

                    if instance.srid:
                        instance.srid_url = (
                            f"http://www.spatialreference.org/ref/{instance.srid.replace(':', '/').lower()}/"
                        )
                    else:
                        raise GeoNodeException(_("Invalid Projection. Dataset is missing CRS!"))

                # Update the instance
                to_update = {}
                if updatemetadata:
                    to_update = {
                        "title": instance.title or instance.name,
                        "abstract": instance.abstract or "",
                        "alternate": instance.alternate,
                    }

                if updatebbox and is_monochromatic_image(instance.thumbnail_url):
                    to_update["thumbnail_url"] = None

                # Save all the modified information in the instance without triggering signals.
                with transaction.atomic():
                    ResourceBase.objects.filter(id=instance.resourcebase_ptr.id).update(**to_update)

                    # to_update['name'] = instance.name,
                    to_update["workspace"] = gs_resource.store.workspace.name
                    to_update["store"] = gs_resource.store.name
                    to_update["subtype"] = instance.subtype
                    to_update["typename"] = instance.alternate
                    to_update["srid"] = instance.srid
                    Dataset.objects.filter(id=instance.id).update(**to_update)

                    # Refresh from DB
                    instance.refresh_from_db()

                if updatemetadata:
                    # Save dataset styles
                    logger.debug(f"... Refresh Legend links for Dataset {instance.title}")
                    try:
                        set_styles(instance, gs_catalog)
                    except Exception as e:
                        logger.warning(e)

                    # Invalidate GeoWebCache for the updated resource
                    try:
                        _stylefilterparams_geowebcache_dataset(instance.alternate)
                        _invalidate_geowebcache_dataset(instance.alternate)
                    except Exception as e:
                        logger.warning(e)

        # Refreshing dataset links
        logger.debug(f"... Creating Default Resource Links for Dataset {instance.title}")
        set_resource_default_links(instance, instance, prune=_is_remote_instance)

        # Refreshing CSW records
        logger.debug(f"... Updating the Catalogue entries for Dataset {instance.title}")
        catalogue_post_save(instance=instance, sender=instance.__class__)
        instance.set_processing_state("PROCESSED")
    except Exception as e:
        logger.exception(e)
        instance.set_processing_state("FAILED")
        raise GeoNodeException(e)
    return instance


def get_dataset_storetype(element):
    return LAYER_SUBTYPES.get(element, element)


def select_relevant_files(allowed_extensions, files):
    """Filter the input files list for relevant files only

    Relevant files are those whose extension is in the ``allowed_extensions``
    iterable.

    :param allowed_extensions: list of strings with the extensions to keep
    :param files: list of django files with the files to be filtered
    """
    result = []
    if files:
        for django_file in files:
            _django_file_name = django_file if isinstance(django_file, str) else django_file.name
            extension = os.path.splitext(_django_file_name)[-1].lower()[1:]
            if extension in allowed_extensions:
                already_selected = _django_file_name in (f if isinstance(f, str) else f.name for f in result)
                if not already_selected:
                    result.append(django_file)
    return result


@dataclasses.dataclass()
class SpatialFilesLayerType:
    base_file: str
    scan_hint: str
    spatial_files: typing.List
    dataset_type: typing.Optional[str] = None


def get_spatial_files_dataset_type(allowed_extensions, files, charset="UTF-8") -> SpatialFilesLayerType:
    """Reutnrs 'vector' or 'raster' whether a file from the allowed extensins has been identified."""
    from geonode.upload.files import scan_file

    allowed_file = select_relevant_files(allowed_extensions, files)
    if not allowed_file or len(allowed_file) != 1:
        return None
    base_file = allowed_file[0]
    spatial_files = scan_file(base_file, charset=charset)
    the_dataset_type = get_dataset_type(spatial_files)
    if the_dataset_type not in (FeatureType.resource_type, Coverage.resource_type):
        return None
    spatial_files_type = SpatialFilesLayerType(
        base_file=base_file,
        scan_hint=None,
        spatial_files=spatial_files,
        dataset_type="vector" if the_dataset_type == FeatureType.resource_type else "raster",
    )

    return spatial_files_type


def get_dataset_type(spatial_files):
    """Returns 'FeatureType.resource_type' or 'Coverage.resource_type' accordingly to the provided SpatialFiles"""
    if spatial_files.archive is not None:
        the_dataset_type = FeatureType.resource_type
    else:
        the_dataset_type = spatial_files[0].file_type.dataset_type
    return the_dataset_type


def get_dataset_capabilities_url(layer, version="1.3.0", access_token=None):
    """
    Generate the layer-specific GetCapabilities URL
    """
    workspace_layername = layer.alternate.split(":") if ":" in layer.alternate else ("", layer.alternate)
    wms_url = settings.GEOSERVER_PUBLIC_LOCATION
    if not layer.remote_service:
        wms_url = f"{wms_url}{'/'.join(workspace_layername)}/ows?service=wms&version={version}&request=GetCapabilities"  # noqa
        if access_token:
            wms_url += f"&access_token={access_token}"
    else:
        wms_url = f"{layer.remote_service.service_url}?service=wms&version={version}&request=GetCapabilities"

    return wms_url


def get_layer_ows_url(layer, access_token=None):
    """
    Generate the layer-specific GetCapabilities URL
    """
    workspace_layername = layer.alternate.split(":") if ":" in layer.alternate else ("", layer.alternate)
    ows_url = settings.GEOSERVER_PUBLIC_LOCATION
    if not layer.remote_service:
        ows_url = f"{ows_url}{'/'.join(workspace_layername)}/ows"  # noqa
        if access_token:
            ows_url += f"?access_token={access_token}"
    else:
        ows_url = f"{layer.remote_service.service_url}"

    return ows_url


def wps_format_is_supported(_format, dataset_type):
    return (_format, dataset_type) in WPS_ACCEPTABLE_FORMATS


def ows_endpoint_in_path(path):
    return (
        re.match(r".*(?<!rest)/(rest)/.*$", path, re.IGNORECASE)
        or re.match(r".*(?<!w[a-z]s)/(w.*s)/.*$", path, re.IGNORECASE)
        or re.match(r".*(?<!ows)/(ows)/.*$", path, re.IGNORECASE)
    )


def _get_from_catalog(url):
    resp = gs_catalog.http_request(url)
    if resp.status_code == 200:
        return resp.content
    else:
        logger.debug(f"Request at {url} returned code {resp.status_code} and content {resp.content}")
        raise Exception(f"Request returned code {resp.status_code}")


def _get_xml(url):
    content = _get_from_catalog(url)
    if isinstance(content, bytes):
        content = content.decode("UTF-8")
    return dlxml.fromstring(content.encode())
