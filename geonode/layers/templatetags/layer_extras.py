import urllib2
import json, os
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


def image_basemap(layername,epsg,out_format):
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
    outputFormat = out_format
    format = 'image/' + str(out_format)

    if epsg == 900913: #transform from 4326 to 3857
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
    bbox = [x0,y0,x1,y1]
    if out_format == 'pdf':
      template_path = os.path.abspath('opt/geonode/geonode/layers/templatetags/pdf_print_template.json')
      if os.path.isfile(template_path):
        with open(template_path,'r') as json_file:
          data = json_file.read()          
        jsontext = json.loads(data)
        jsontext['mapTitle'] = layer.name.title().replace('_',' ')
        jsontext['abstract'] = layer.abstract
        jsontext['purpose'] = layer.purpose
    else:
      template_path = os.path.abspath('opt/geonode/geonode/layers/templatetags/image_print_template.json')
      if os.path.isfile(template_path):
        with open(template_path,'r') as json_file:
          data = json_file.read()
        jsontext = json.loads(data)
        jsontext['layers'][0]['format'] = format
        jsontext['layers'][1]['format'] = format    

    jsontext['srs'] = to_srs_str
    jsontext['outputFormat'] = outputFormat
    jsontext['outputFilename'] = layer.name
    # jsontext['layers'][0]['baseURL'] = settings.OGC_SERVER['default']['LOCATION'] + 'wms?SERVICE=WMS&'
    jsontext['layers'][0]['baseURL'] = baseURL + 'wms?SERVICE=WMS&' #baseURL for local
    jsontext['layers'][1]['baseURL'] = baseURL + 'wms?SERVICE=WMS&' #baseURL for local
    jsontext['layers'][0]['layers'] = [str(layer.typename)]
    jsontext['pages'][0]['bbox'] = bbox
    jsonmini = json.dumps(jsontext,separators=(',',':'))
    urlencoded = urllib.quote(jsonmini)
    # print urlencoded
    
    spec = baseURL +'pdf/print.pdf?spec=' + urlencoded
    # print spec
    return spec

def prep_basemap(link,epsg,format):
    remove_prefix = str(link.split('layers=')[1]).split('&width')[0]
    layername = str(remove_prefix.split('%3A')[1]).split('&width')[0]
    # layername = 'geonode:' + str(layername)
    link = image_basemap(layername,epsg,format)
    return link

# applies for wfs, wcs layer types


def get_prs92_download_url(link):
    link = link.get_download_url()
    if 'GeoTIFF' in str(link):
        epsg4683 = 'crs=EPSG%3A4683'
        temp = link.split('crs=EPSG%3A32651')
        link = temp[0] + epsg4683 + temp[1]
    elif 'image%2Fpng' in str(link):
        link = prep_basemap(link,900193,'png')
        return link
    elif 'image%2Fjpeg' in str(link): #remove this
        link = prep_basemap(link,900913,'jpeg')
        return link
    elif '%2Fpdf' in str(link): #remove this
        link = prep_basemap(link,900913,'pdf')
    elif 'SHAPE-ZIP' in str(link) or 'kml' in str(link):
        link = link + '&srsName=EPSG:4683'

    return link

    if 'image%2Fpng' in str(link):
        link = prep_basemap(link,4326,'png')
        return link
    elif 'image%2Fjpeg' in str(link): #remove this
        link = prep_basemap(link,4326,'jpeg')
        return link
    elif '%2Fpdf' in str(link): #remove this
        link = prep_basemap(link,4326,'pdf')
        return link
    else:
        return link

register.filter('get_layer_download_url', get_layer_download_url)
register.filter('get_prs92_download_url', get_prs92_download_url)

