# -*- coding: utf-8 -*-
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

import sys, os
import logging
import re
import errno
import uuid
import datetime
from itertools import cycle, izip

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import pre_delete

from geonode.utils import _user, _password, ogc_server_settings

from geoserver.catalog import Catalog, FailedRequestError
from geoserver.store import CoverageStore, DataStore
from geoserver.workspace import Workspace

from dialogos.models import Comment
from agon_ratings.models import OverallRating

logger = logging.getLogger(__name__)

_punc = re.compile(r"[\.:]") #regex for punctuation that confuses restconfig
_foregrounds = ["#ffbbbb", "#bbffbb", "#bbbbff", "#ffffbb", "#bbffff", "#ffbbff"]
_backgrounds = ["#880000", "#008800", "#000088", "#888800", "#008888", "#880088"]
_marks = ["square", "circle", "cross", "x", "triangle"]
_style_contexts = izip(cycle(_foregrounds), cycle(_backgrounds), cycle(_marks))
_default_style_names = ["point", "line", "polygon", "raster"]

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
    raster = _add_sld_boilerplate(_raster_template),
    polygon = _add_sld_boilerplate(_polygon_template),
    line = _add_sld_boilerplate(_line_template),
    point = _add_sld_boilerplate(_point_template)
)

def _style_name(resource):
    return _punc.sub("_", resource.store.workspace.name + ":" + resource.name)

def get_sld_for(layer):
    # FIXME: GeoServer sometimes fails to associate a style with the data, so
    # for now we default to using a point style.(it works for lines and
    # polygons, hope this doesn't happen for rasters  though)
    name = layer.default_style.name if layer.default_style is not None else "point"

    # FIXME: When gsconfig.py exposes the default geometry type for vector
    # layers we should use that rather than guessing based on the auto-detected
    # style.

    if name in _style_templates:
        fg, bg, mark = _style_contexts.next()
        return _style_templates[name] % dict(name=layer.name, fg=fg, bg=bg, mark=mark)
    else:
        return None

def fixup_style(cat, resource, style):
    logger.debug("Creating styles for layers associated with [%s]", resource)
    layers = cat.get_layers(resource=resource)
    logger.info("Found %d layers associated with [%s]", len(layers), resource)
    for lyr in layers:
        if lyr.default_style.name in _style_templates:
            logger.info("%s uses a default style, generating a new one", lyr)
            name = _style_name(resource)
            if style is None:
                sld = get_sld_for(lyr)
            else: 
                sld = style.read()
            logger.info("Creating style [%s]", name)
            style = cat.create_style(name, sld)
            lyr.default_style = cat.get_style(name)
            logger.info("Saving changes to %s", lyr)
            cat.save(lyr)
            logger.info("Successfully updated %s", lyr)

def cascading_delete(cat, layer_name):
    resource = None
    try:
        if layer_name.find(':') != -1:
            workspace, name = layer_name.split(':')
            ws = cat.get_workspace(workspace)
            if ws == None:
                logger.debug('cascading delete was called on a layer where the workspace was not found')
                return
            resource = cat.get_resource(name, workspace = workspace)
        else:
            resource = cat.get_resource(layer_name)
    except EnvironmentError, e: 
      if e.errno == errno.ECONNREFUSED:
        msg = ('Could not connect to geoserver at "%s"'
               'to save information for layer "%s"' % (
               ogc_server_settings.LOCATION, layer_name)
              )
        logger.warn(msg, e)
        return None
      else:
        raise e

    if resource is None:
        # If there is no associated resource,
        # this method can not delete anything.
        # Let's return and make a note in the log.
        logger.debug('cascading_delete was called with a non existent resource')
        return
    resource_name = resource.name
    lyr = cat.get_layer(resource_name)
    if(lyr is not None): #Already deleted
        store = resource.store
        styles = lyr.styles + [lyr.default_style]
        cat.delete(lyr)
        for s in styles: 
            if s is not None and s.name not in _default_style_names:
                try:
                    cat.delete(s, purge=True)
                except FailedRequestError as e:
                    # Trying to delete a shared style will fail
                    # We'll catch the exception and log it.
                    logger.debug(e)

        cat.delete(resource)
        if store.resource_type == 'dataStore' and 'dbtype' in store.connection_parameters and store.connection_parameters['dbtype'] == 'postgis':
            delete_from_postgis(resource_name)
        else:
            try:
                cat.delete(store)
            except FailedRequestError as e:
                # Trying to delete a shared store will fail 
                # We'll catch the exception and log it.
                logger.debug(e) 


def delete_from_postgis(resource_name):
    """
    Delete a table from PostGIS (because Geoserver won't do it yet);
    to be used after deleting a layer from the system.
    """
    import psycopg2
    dsname = ogc_server_settings.DATASTORE
    db = ogc_server_settings.datastore_db
    conn=psycopg2.connect("dbname='" + db['NAME'] + "' user='" + db['USER'] + "'  password='" + db['PASSWORD'] + "' port=" + db['PORT'] + " host='" + db['HOST'] + "'")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DropGeometryTable ('%s')" %  resource_name)
        conn.commit()
    except Exception, e:
        logger.error("Error deleting PostGIS table %s:%s", resource_name, str(e))
    finally:
        conn.close()

def gs_slurp(ignore_errors=True, verbosity=1, console=None, owner=None, workspace=None, store=None, filter=None, skip_unadvertised=False, remove_deleted=False):
    """Configure the layers available in GeoServer in GeoNode.

       It returns a list of dictionaries with the name of the layer,
       the result of the operation and the errors and traceback if it failed.
    """

    # avoid circular import problem
    from geonode.layers.models import set_attributes

    if console is None:
        console = open(os.devnull, 'w')

    if verbosity > 1:
        print >> console, "Inspecting the available layers in GeoServer ..."
    cat = Catalog(ogc_server_settings.internal_rest, _user, _password)
    if workspace is not None:
        workspace = cat.get_workspace(workspace)
        resources = cat.get_resources(workspace=workspace)
    elif store is not None:
        store = cat.get_store(store)
        resources = cat.get_resources(store=store)
    else:
        resources = cat.get_resources(workspace=workspace)
    if remove_deleted:
        resources_for_delete_compare = resources[:]
        workspace_for_delete_compare = workspace
        # filter out layers for delete comparison with GeoNode layers by following criteria:
        # enabled = true, if --skip-unadvertised: advertised = true, but disregard the filter parameter in the case of deleting layers
        resources_for_delete_compare = [k for k in resources_for_delete_compare if k.enabled == "true"]
        if skip_unadvertised: resources_for_delete_compare = [k for k in resources_for_delete_compare if k.advertised == "true" or k.advertised == None]
    if filter:
        resources = [k for k in resources if filter in k.name]

    # filter out layers depending on enabled, advertised status:
    resources = [k for k in resources if k.enabled == "true"]
    if skip_unadvertised: resources = [k for k in resources if k.advertised == "true" or k.advertised == None]
    
    # TODO: Should we do something with these?
    # i.e. look for matching layers in GeoNode and also disable? 
    disabled_resources = [k for k in resources if k.enabled == "false"]
    
    number = len(resources)
    if verbosity > 1:
        msg = "Found %d layers, starting processing" % number
        print >> console, msg
    output = {
        'stats': {
            'failed':0,
            'updated':0,
            'created':0,
            'deleted':0,
        },
        'layers': [],
        'deleted_layers': []
    }
    start = datetime.datetime.now()
    for i, resource in enumerate(resources):
        name = resource.name
        store = resource.store
        workspace = store.workspace
        try:
            # Avoid circular import problem
            from geonode.layers.models import Layer
            layer, created = Layer.objects.get_or_create(name=name, defaults = {
                "workspace": workspace.name,
                "store": store.name,
                "storeType": store.resource_type,
                "typename": "%s:%s" % (workspace.name.encode('utf-8'), resource.name.encode('utf-8')),
                "title": resource.title or 'No title provided',
                "abstract": resource.abstract or 'No abstract provided',
                "owner": owner,
                "uuid": str(uuid.uuid4())
            })
            layer.save()
            # recalculate the layer statistics
            set_attributes(layer, overwrite=True)

        except Exception, e:
            if ignore_errors:
                status = 'failed'
                exception_type, error, traceback = sys.exc_info()
            else:
                if verbosity > 0:
                    msg = "Stopping process because --ignore-errors was not set and an error was found."
                    print >> sys.stderr, msg
                raise Exception('Failed to process %s' % resource.name.encode('utf-8'), e), None, sys.exc_info()[2]
        else:
            if created:
                layer.set_default_permissions()
                status = 'created'
                output['stats']['created']+=1
            else:
                status = 'updated'
                output['stats']['updated']+=1

        msg = "[%s] Layer %s (%d/%d)" % (status, name, i+1, number)
        info = {'name': name, 'status': status}
        if status == 'failed':
            output['stats']['failed']+=1
            info['traceback'] = traceback
            info['exception_type'] = exception_type
            info['error'] = error
        output['layers'].append(info)
        if verbosity > 0:
            print >> console, msg
    
    if remove_deleted:
        q = Layer.objects.filter()
        if workspace_for_delete_compare is not None:
            if isinstance(workspace_for_delete_compare, Workspace): q = q.filter(workspace__exact=workspace_for_delete_compare.name)
            else: q = q.filter(workspace__exact=workspace_for_delete_compare)
        if store is not None:
            if isinstance(store, CoverageStore) or isinstance(store, DataStore): q = q.filter(store__exact=store.name)
            else: q = q.filter(store__exact=store)
        logger.debug("Executing 'remove_deleted' logic")
        logger.debug("GeoNode Layers Found:")
        
        # compare the list of GeoNode layers obtained via query/filter with valid resources found in GeoServer 
        # filtered per options passed to updatelayers: --workspace, --store, --skip-unadvertised
        # add any layers not found in GeoServer to deleted_layers (must match workspace and store as well):
        deleted_layers = []
        for layer in q:
            logger.debug("GeoNode Layer info: name: %s, workspace: %s, store: %s", layer.name, layer.workspace, layer.store)
            layer_found_in_geoserver = False
            for resource in resources_for_delete_compare:
                #if layer.name matches a GeoServer resource, check also that workspace and store match, mark valid:
                if layer.name == resource.name:
                    if layer.workspace == resource.workspace.name and layer.store == resource.store.name:
                        logger.debug("Matches GeoServer layer: name: %s, workspace: %s, store: %s", resource.name,resource.workspace.name, resource.store.name)
                        layer_found_in_geoserver = True
            if not layer_found_in_geoserver: 
                logger.debug("----- Layer %s not matched, marked for deletion ---------------", layer.name)
                deleted_layers.append(layer)
        
        number_deleted = len(deleted_layers)
        if verbosity > 1:
            msg = "\nFound %d layers to delete, starting processing" % number_deleted if number_deleted > 0 else "\nFound %d layers to delete" % number_deleted
            print >> console, msg
        
        for i, layer in enumerate(deleted_layers):
            logger.debug("GeoNode Layer to delete: name: %s, workspace: %s, store: %s", layer.name, layer.workspace, layer.store)
            try:
                from geonode.layers.models import geoserver_pre_delete
                #delete ratings, comments, and taggit tags:
                ct = ContentType.objects.get_for_model(layer)
                OverallRating.objects.filter(content_type = ct, object_id = layer.id).delete()
                Comment.objects.filter(content_type = ct, object_id = layer.id).delete()
                layer.keywords.clear()
                
                pre_delete.disconnect(geoserver_pre_delete, sender=Layer)
                layer.delete()
                output['stats']['deleted']+=1
                status = "delete_succeeded"
            except Exception, e:
                status = "delete_failed"
            finally:
                pre_delete.connect(geoserver_pre_delete, sender=Layer)
            
            msg = "[%s] Layer %s (%d/%d)" % (status, layer.name, i+1, number_deleted)
            info = {'name': layer.name, 'status': status}
            if status == "delete_failed":
                exception_type, error, traceback = sys.exc_info()
                info['traceback'] = traceback
                info['exception_type'] = exception_type
                info['error'] = error
            output['deleted_layers'].append(info)
            if verbosity > 0:
                print >> console, msg

    finish = datetime.datetime.now()
    td = finish - start
    output['stats']['duration_sec'] = td.microseconds / 1000000 + td.seconds + td.days * 24 * 3600
    return output

def get_stores(store_type = None):
    cat = Catalog(ogc_server_settings.internal_rest, _user, _password)
    stores = cat.get_stores()
    store_list = []
    for store in stores:
        store.fetch()
        stype = store.dom.find('type').text.lower()
        if store_type and store_type.lower() == stype:
            store_list.append({'name':store.name, 'type': stype})
        elif store_type is None:
            store_list.append({'name':store.name, 'type': stype})
    return store_list
