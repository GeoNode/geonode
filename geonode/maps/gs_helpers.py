from itertools import cycle, izip
from geoserver.catalog import FailedRequestError
import sys
import logging
import re
from django.conf import settings


logger = logging.getLogger("geonode.maps.gs_helpers")

_punc = re.compile(r"[\.:]") #regex for punctuation that confuses restconfig
_foregrounds = ["#ffbbbb", "#bbffbb", "#bbbbff", "#ffffbb", "#bbffff", "#ffbbff"]
_backgrounds = ["#880000", "#008800", "#000088", "#888800", "#008888", "#880088"]
_marks = ["square", "circle", "cross", "x", "triangle"]
_style_contexts = izip(cycle(_foregrounds), cycle(_backgrounds), cycle(_marks))

def _add_sld_boilerplate(symbolizer):
    """
    Wrap an XML snippet representing a single symbolizer in the approperiate
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
    # layers we should use that rather than guessing based on the autodetected
    # style.

    if name in _style_templates:
        fg, bg, mark = _style_contexts.next()
        return _style_templates[name] % dict(name=layer.name, fg=fg, bg=bg, mark=mark)
    else:
        return None

def fixup_style(cat, resource, style):
    logger.debug("Creating styles for layers associated with [%s]", resource)
    layers = cat.get_layers(resource=resource)
    logger.debug("Found %d layers associated with [%s]", len(layers), resource)
    for lyr in layers:
        if lyr.default_style.name in _style_templates:
            logger.debug("%s uses a default style, generating a new one", lyr)
            name = _style_name(resource)
            if style is None:
                sld = get_sld_for(lyr)
            else:
                sld = style.read()
            logger.debug("Creating style [%s]", name)
            style = cat.create_style(name, sld)
            lyr.default_style = cat.get_style(name)
            logger.debug("Saving changes to %s", lyr)
            cat.save(lyr)
            logger.debug("Successfully updated %s", lyr)

def cascading_delete(cat, resource):
    if resource is None:
        # If there is no associated resource,
        # this method can not delete anything.
        # Let's return and make a note in the log.
        logger.debug('cascading_delete was called with a non existant resource')
        return
    resource_name = resource.name
    lyr = cat.get_layer(resource_name)
    if(lyr is not None): #Already deleted
        store = resource.store
        styles = lyr.styles + [lyr.default_style]
        cat.delete(lyr)
        for s in styles:
            if s is not None:
                try:
                    cat.delete(s, purge=True)
                except FailedRequestError as e:
                    # Trying to delete a shared style will fail
                    # We'll catch the exception and log it.
                    logger.debug(e)

        try:
            cat.delete(resource) #This will fail on Geoserver 2.4+
        except Exception as e:
            import traceback
            traceback.print_exc(sys.exc_info())
            err_msg = 'Error deleting resource "%s".  Expected in Geoserver 2.4+\nError: %s' % (resource_name, str(e))
            #print err_msg
            logger.error(err_msg)
            # continue on....

        if store.resource_type == 'dataStore' and 'dbtype' in store.connection_parameters and store.connection_parameters['dbtype'] == 'postgis':
            delete_from_postgis(resource_name, store.name)
        else:
            cat.delete(store)



def delete_from_postgis(resource_name, store_name):
    """
    Delete a table from PostGIS (because Geoserver won't do it yet);
    to be used after deleting a layer from the system.
    """
    import psycopg2
    conn=psycopg2.connect("dbname='" + store_name + "' user='" + settings.DB_DATASTORE_USER + "'  password='" + settings.DB_DATASTORE_PASSWORD + "' port=" + settings.DB_DATASTORE_PORT + " host='" + settings.DB_DATASTORE_HOST + "'")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DropGeometryTable ('%s')" %  resource_name)
        conn.commit()
    except Exception, e:
        logger.error("Error deleting PostGIS table %s:%s", resource_name, str(e))
    finally:
        conn.close()


def get_postgis_bbox(resource_name, store_name):
    """
    Update the native and latlong bounding box for a layer via PostGIS.
    Doing it via Geoserver is too resource-intensive
    """
    import psycopg2
    conn=psycopg2.connect("dbname='" + store_name + "' user='" + settings.DB_DATASTORE_USER + "'  password='" + settings.DB_DATASTORE_PASSWORD + "' port=" + settings.DB_DATASTORE_PORT + " host='" + settings.DB_DATASTORE_HOST + "'")
    try:
        cur = conn.cursor()
        cur.execute("select ST_EXTENT(the_geom) as bbox, ST_EXTENT(ST_Transform(the_geom,4326)) as llbbox from \"%s\"" %  resource_name)
        rows = cur.fetchall()
        return rows
    except Exception, e:
        logger.info("Error retrieving bbox for PostGIS table %s:%s", resource_name, str(e))
    finally:
        conn.close()
