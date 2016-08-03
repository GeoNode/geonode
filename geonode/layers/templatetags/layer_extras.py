import urllib2
import json
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


def image_basemap(layername,epsg,out_format,format_options):
	text = '''{
	  "units":"degrees",
	  "geodetic":"false",
	  "srs":"",
	  "layout":"Image",
	  "dpi":300,
	  "outputFilename":"",
	  "outputFormat":"",
	  "comment": "",
	  "mapTitle": "",
	  "layers": [
	    {
	      "baseURL": "",
	      "opacity": 1,
	      "singleTile": false,
	      "type": "WMS",
	      "layers": [
	        
	      ],
	      "format": "",
	      "styles": [
	        ""
	      ],
	      "customParams": {
	        "TRANSPARENT": true,
	        "TILED": true
	      }
	    },
	    {
	      "baseURL": "",
	      "opacity": 1,
	      "singleTile": false,
	      "type": "WMS",
	      "layers": [
	        "osm:osm"
	      ],
	      "format": "",
	      "styles": [
	        ""
	      ],
	      "customParams": {
	        "TRANSPARENT": true,
	        "TILED": true
	      }
	    }
	  ],
	  "pages": [
	    {
	      "bbox": [],
	      "rotation": 0
	    }
	  ]
	}'''
	cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
	            username=settings.OGC_SERVER['default']['USER'],
	            password=settings.OGC_SERVER['default']['PASSWORD'])
	layer = Layer.objects.get(name=layername)
	geoserver_layer = cat.get_layer(layer.name)
	layer_projection = geoserver_layer.resource.projection
	layer_projection_epsg = layer_projection.split(':')[1]
	bbox_string = layer.bbox_string.split(',')
	x0 = float(bbox_string[0])
	y0 = float(bbox_string[1])
	x1 = float(bbox_string[2])
	y1 = float(bbox_string[3])
	#for mapfish printing
	to_srs = epsg
	# if 'lipad' in settings.SITEURL:
	# 	baseURL = settings.OGC_SERVER['default']['LOCATION']
	# else:
	baseURL = settings.OGC_SERVER['default']['PUBLIC_LOCATION']
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
	jsontext = json.loads(text)
	jsontext['srs'] = to_srs_str
	jsontext['outputFormat'] = outputFormat
	jsontext['outputFilename'] = layer.name
	jsontext['layers'][0]['baseURL'] = settings.OGC_SERVER['default']['LOCATION'] + 'wms?SERVICE=WMS&'
	jsontext['layers'][1]['baseURL'] = settings.OGC_SERVER['default']['LOCATION'] + 'wms?SERVICE=WMS&'
	jsontext['layers'][0]['layers'] = [str(layer.typename)]
	jsontext['layers'][0]['format'] = format
	jsontext['layers'][1]['format'] = format
	jsontext['pages'][0]['bbox'] = bbox
	jsonmini = json.dumps(jsontext,separators=(',',':'))
	urlencoded = urllib.quote(jsonmini)
	# print urlencoded
	if format_options == 'pl1':
		spec = baseURL +'pdf/print.pdf?spec=' + urlencoded + '&format_options=layout:phillidar1'
	elif format_options == 'pl2':
		spec = baseURL +'pdf/print.pdf?spec=' + urlencoded + '&format_options=layout:phillidar1'
	else:
		spec = baseURL +'pdf/print.pdf?spec=' + urlencoded
	# print spec
	return spec

def prep_basemap(link,epsg,format,format_options):
	# sample download link
	# http://geonode1:8080/geoserver/wms?layers=geonode%3Alidar_panay&width=464&bbox=121.85450531172008%2C10.374483313884495%2C123.24705566155922%2C12.025011538981765&service=WMS&format=image%2Fjpeg&srs=EPSG%3A4326&request=GetMap&height=550
	remove_prefix = str(link.split('layers=')[1]).split('&width')[0]
	layername = str(remove_prefix.split('%3A')[1]).split('&width')[0]
	# layername = 'geonode:' + str(layername)
	link = image_basemap(layername,epsg,format,format_options)
	return link

def get_prs92_download_url(link): #wfs, wcs
	link = link.get_download_url()
	if 'GeoTIFF' in str(link) or 'ArcGrid' in str(link):
		epsg4683 = 'crs=EPSG%3A4683'
		temp = link.split('crs=EPSG%3A32651')
		link = temp[0] + epsg4683 + temp[1]
	elif 'image%2Fpng' in str(link):
		link = prep_basemap(link,900913,'png','')
		return link
	elif 'image%2Fjpeg' in str(link): #remove this
		link = prep_basemap(link,900913,'jpeg','')
		return link
	elif 'SHAPE-ZIP' in str(link) or 'kml' in str(link):
		link = link + '&srsName=EPSG:4683'
	return link

def prs92_download_url_pl1(link): #FHM
	link = link.get_download_url()
	if 'image%2Fpng' in str(link):
		link = prep_basemap(link,900913,'png','pl1')
		return link
	elif 'image%2Fjpeg' in str(link): #remove this
		link = prep_basemap(link,900913,'jpeg','pl1')
		return link
	elif 'SHAPE-ZIP' in str(link) or 'kml' in str(link):
		link = link + '&srsName=EPSG:4683'
	link = link + '&format_options=layout:phillidar1'
	return link

def prs92_download_url_pl2(link): #PL2 resource layers
	link = link.get_download_url()
	if 'image%2Fpng' in str(link):
		link = prep_basemap(link,900913,'png','pl2')
		return link
	elif 'image%2Fjpeg' in str(link): #remove this
		link = prep_basemap(link,900913,'jpeg','pl2')
		return link
	elif 'SHAPE-ZIP' in str(link) or 'kml' in str(link):
		link = link + '&srsName=EPSG:4683'
	link = link + '&format_options=layout:phillidar2'
	return link

def get_layer_download_url(link): # Only one argument.
	link = link.get_download_url()
	if 'image%2Fpng' in str(link):
		link = prep_basemap(link,4326,'png','')
		return link
	elif 'image%2Fjpeg' in str(link): #remove this
		link = prep_basemap(link,4326,'jpeg','')
		return link
	else:
		return link

register.filter('get_layer_download_url', get_layer_download_url)
register.filter('get_prs92_download_url', get_prs92_download_url)
register.filter('prs92_download_url_pl1', prs92_download_url_pl1)
register.filter('prs92_download_url_pl2', prs92_download_url_pl2)

