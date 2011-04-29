from itertools import cycle, izip
from django.conf import settings
import logging
import re
import psycopg2

logger = logging.getLogger("geonode.maps.gs_helpers")

_punc = re.compile(r"[\.:]") #regex for punctuation that confuses restconfig
_foregrounds = ["#ffbbbb", "#bbffbb", "#bbbbff", "#ffffbb", "#bbffff", "#ffbbff"]
_backgrounds = ["#880000", "#008800", "#000088", "#888800", "#008888", "#880088"]
_marks = ["square", "circle", "star", "cross", "x", "triangle"]
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
  </Stroke>
</PolygonSymbolizer>
"""

_line_template = """
<LineSymbolizer>
  <Stroke>
    <CssParameter name="stroke">%(bg)s</CssParameter>
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

def fixup_style(cat, resource, style):
    lyr = cat.get_layer(name=resource.name)
    if lyr:
        if lyr.default_style and lyr.default_style.name in _style_templates:
            name = _style_name(resource)
            if (cat.get_style(name)):
                iter = 1
                while cat.get_style(name):
                    name = name + '_c' + str(iter)
                    iter+=1
            fg, bg, mark = _style_contexts.next()
            if style is None:
                sld = _style_templates[lyr.default_style.name] % dict(name=name, fg=fg, bg=bg, mark=mark)
            else: 
                sld = style.read()
            style = cat.create_style(name, sld)
            lyr.default_style = cat.get_style(name)
            cat.save(lyr)

def cascading_delete(cat, resource):
    #Maybe it's already been deleted from geoserver?
    logger.debug("CASCADE DELETE %s", resource.name if resource else 'NULL')
    if resource:
        lyr = cat.get_layer(resource.name)

        styles = lyr.styles + [lyr.default_style]
        try:
            cat.delete(lyr)
            logger.debug('Deleted layer')
        except:
            logger.error('Error deleting layer [%s]', resource.name)
        for s in styles:
            if s is not None:
                try:
                    cat.delete(s, purge=True)
                    logger.debug('Deleted style')
                except:
                    logger.error('Error deleting style for %s', resource.name)
        store = resource.store
        resource_name = resource.name
        try:
            cat.delete(resource)
            logger.debug('Deleted resource')
        except:
            logger.error("Error deleting resource")
        try:
            logger.debug('STORE NAME:' + store.name)
            ##TODO: get rid of this conditional statement
            if store.name != 'wmdata':
                cat.delete(store)

            delete_from_postgis(resource_name)
        except Exception, ex:
            logger.error("Error deleting store, [%s]", str(ex))
        return True
    else:
        logger.error('Error deleting layer & styles - not found in geoserver')
        return False


def delete_from_postgis(resource_name):
    try:
        conn=psycopg2.connect("dbname='" + settings.POSTGIS_NAME + "' user='" + settings.POSTGIS_USER + "'  password='" + settings.POSTGIS_PASSWORD + "' port=" + settings.POSTGIS_PORT + " host='" + settings.POSTGIS_HOST + "'")
        cur = conn.cursor()
        cur.execute("""select DropGeometryTable('""" + resource_name  + """')""")
        conn.commit()
    except Exception, e:
        logger.error("Error deleting PostGIS table %s:%s", resource_name, str(e))
    finally:
        if conn:
            conn.close()

