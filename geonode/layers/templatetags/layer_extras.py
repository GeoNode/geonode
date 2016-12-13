import urllib2
import json
import os
from django.core.urlresolvers import resolve
import urllib
from geonode.layers.models import Layer
import geonode.settings as settings
from geoserver.catalog import Catalog
from osgeo import ogr
from osgeo import osr
from django import template
register = template.Library()
from pprint import pprint


def prs92_projection(x0, y0, x1, y1):
    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)
    target = osr.SpatialReference()
    target.ImportFromEPSG(3857)
    transform = osr.CoordinateTransformation(source, target)
    point_str = "POINT (" + str(x0) + ' ' + str(y0) + ")"
    point1 = ogr.CreateGeometryFromWkt(str(point_str))
    point1.Transform(transform)
    # print point1.ExportToWkt()
    x0 = point1.GetX()
    y0 = point1.GetY()
    point_str = "POINT (" + str(x1) + ' ' + str(y1) + ")"
    point2 = ogr.CreateGeometryFromWkt(str(point_str))
    point2.Transform(transform)
    # print point2.ExportToWkt()
    x1 = point2.GetX()
    y1 = point2.GetY()

    return x0, y0, x1, y1

# extracts layer name and filetype format options


def analyze_link(link):
    # print '***** L I N K *****'
    # pprint(link)
    # layer_name=link.split('geonode%3A')[1].split('%22%5D%2C%22format')[0]
    layer_name = link.split('geonode%3A')[1].split('/download/wms')[0]
    layer = Layer.objects.get(name=layer_name)
    layout = 'phil-lidar1'
    if 'wms' in link:  # for wms layers
        if 'PhilLiDAR2' in layer.keyword_list():
            layout = 'phil-lidar2'
    return layer, layout

##


def image_basemap(link, epsg, filetype):
    # text = ''''''
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                  username=settings.OGC_SERVER['default']['USER'],
                  password=settings.OGC_SERVER['default']['PASSWORD'])
    baseURL = settings.OGC_SERVER['default']['PUBLIC_LOCATION']

    # get layer name
    layer, layout = analyze_link(link)
    geoserver_layer = cat.get_layer(layer.name)
    layer_projection = geoserver_layer.resource.projection
    layer_projection_epsg = layer_projection.split(':')[1]
    bbox_string = layer.bbox_string.split(',')
    x0 = float(bbox_string[0])
    y0 = float(bbox_string[1])
    x1 = float(bbox_string[2])
    y1 = float(bbox_string[3])

    # for mapfish printing
    to_srs = epsg
    # if 'lipad' in settings.SITEURL:
    #   baseURL = settings.OGC_SERVER['default']['LOCATION']
    # else:
    to_srs_str = 'EPSG:' + str(to_srs)
    # filetype_cp = filetype

    # transform projection from 4326 to 3857
    if epsg == 900913:
        x0, y0, x1, y1 = prs92_projection(x0, y0, x1, y1)

    # bbox values
    bbox = [x0, y0, x1, y1]

    # json template for requested filetype
    template_path = os.path.abspath(
        '/opt/geonode/geonode/layers/templatetags/pdf_print_template.json')
    if os.path.isfile(template_path):
        #   with open(template_path,'r') as json_file:
        #     data = json_file.read()
        jsontext = json.load(open(template_path, 'r'))
        jsontext['mapTitle'] = layer.title.title()
        jsontext['abstract'] = layer.abstract
        jsontext['purpose'] = layer.purpose
        if layer.purpose is None:
            jsontext['purpose'] = 'No purpose provided'
        jsontext['srs'] = to_srs_str
        jsontext['outputFormat'] = filetype
        jsontext['outputFilename'] = layer.name
        # jsontext['layers'][0]['baseURL'] = settings.OGC_SERVER['default']['LOCATION'] + 'wms?SERVICE=WMS&'
        jsontext['layers'][0]['baseURL'] = baseURL + \
            'wms?SERVICE=WMS&'  # baseURL for local
        jsontext['layers'][1]['baseURL'] = baseURL + \
            'wms?SERVICE=WMS&'  # baseURL for local
        jsontext['layers'][0]['layers'] = [str(layer.typename)]
        jsontext['layout'] = layout
        # jsontext['layout'] = 'A4 portrait'
        jsontext['pages'][0]['bbox'] = bbox
        legendurl = baseURL + 'wms?request=GetLegendGraphic&format=image/png&LAYER=' + str(layer.typename)
        jsontext['legends'][0]['classes'][0]['icons'][0] = legendurl
        # jsontext['legends'][0]['classes'][0]['icons'] = ['https://lipad-tst.dream.upd.edu.ph/geoserver/wms?request=GetLegendGraphic&format=image/png&WIDTH=20&HEIGHT=20&LAYER=geonode:m_bulacan_p_bulacan_fh5yr_10m&legend_options=fontAntiAliasing:true;fontSize:12;forceLabels:on']

        print '******************** J S O N ********************'
        pprint(jsontext)

        jsonmini = json.dumps(jsontext, separators=(',', ':'))
        urlencoded = urllib.quote(jsonmini)
        # print urlencoded

        spec = baseURL + 'pdf/print.pdf?spec=' + urlencoded
        # print spec
        return spec
    else:
        print 'TEMPLATE NOT FOUND'

# applies for wfs, wcs layer types


def get_prs92_download_url(link):
    link = link.get_download_url()
    return link
    # Ignore the ff. for now
    if 'GeoTIFF' in str(link):
        epsg4683 = 'crs=EPSG%3A4683'
        temp = link.split('crs=EPSG%3A32651')
        link = temp[0] + epsg4683 + temp[1]
    elif 'image%2Fpng' in str(link):
        link = image_basemap(link, 900193, 'png')
        return link
    elif 'image%2Fjpeg' in str(link):  # remove this
        link = image_basemap(link, 900913, 'jpeg')
        return link
    elif '%2Fpdf' in str(link):  # remove this
        link = image_basemap(link, 900913, 'pdf')
    elif 'SHAPE-ZIP' in str(link) or 'kml' in str(link):
        link = link + '&srsName=EPSG:4683'
    return link


def get_layer_download_url(link):  # Only one argument.
    link = link.get_download_url()
    return link
    # Ignore the ff. for now
    # format_options=check_layout(link)

    if 'image%2Fpng' in str(link):
        link = image_basemap(link, 4326, 'png')
        return link
    elif 'image%2Fjpeg' in str(link):  # remove this
        link = image_basemap(link, 4326, 'jpeg')
        return link
    elif '%2Fpdf' in str(link):  # remove this
        link = image_basemap(link, 4326, 'pdf')
        return link
    else:
        return link

register.filter('get_layer_download_url', get_layer_download_url)
register.filter('get_prs92_download_url', get_prs92_download_url)
