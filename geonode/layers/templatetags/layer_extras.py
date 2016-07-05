import urllib2
import json
from django.core.urlresolvers import resolve

from django import template
register = template.Library()
from pprint import pprint

def get_layer_download_url(link): # Only one argument.
    return link.get_download_url()

def get_prs92_download_url(link): #wfs, wcs
	link = link.get_download_url()
	if 'GeoTIFF' in str(link) or 'ArcGrid' in str(link):
		epsg4683 = 'crs=EPSG%3A4683'
		temp = link.split('crs=EPSG%3A32651')
		link = temp[0] + epsg4683 + temp[1]
	elif 'image%2Fpng' in str(link) or 'image%2Fjpeg' in str(link): #remove this
		epsg4683 = 'srs=EPSG%3A4683'
		temp = link.split('srs=EPSG%3A4326')
		link = temp[0] + epsg4683 + temp[1]
	elif 'SHAPE-ZIP' in str(link):
		link = link + '&srsName=EPSG:4683'
	return link

def prs92_download_url_pl1(link):
	link = link.get_download_url()
	if 'image%2Fpng' in str(link) or 'image%2Fjpeg' in str(link):
		epsg4683 = 'srs=EPSG%3A4683'
		temp = link.split('srs=EPSG%3A4326')
		link = temp[0] + epsg4683 + temp[1]
	elif 'SHAPE-ZIP' in str(link):
		link = link + '&srsName=EPSG:4683'
	link = link + '&format_options=layout:phillidar1'
	return link

def prs92_download_url_pl2(link):
	link = link.get_download_url()
	if 'image%2Fpng' in str(link) or 'image%2Fjpeg' in str(link):
		epsg4683 = 'srs=EPSG%3A4683'
		temp = link.split('srs=EPSG%3A4326')
		link = temp[0] + epsg4683 + temp[1]
	elif 'SHAPE-ZIP' in str(link):
		link = link + '&srsName=EPSG:4683'
	link = link + '&format_options=layout:phillidar2'
	return link

register.filter('get_layer_download_url', get_layer_download_url)
register.filter('get_prs92_download_url', get_prs92_download_url)
register.filter('prs92_download_url_pl1', prs92_download_url_pl1)
register.filter('prs92_download_url_pl2', prs92_download_url_pl2)

