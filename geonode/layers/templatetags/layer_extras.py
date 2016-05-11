import urllib2
import json
from django.core.urlresolvers import resolve

from django import template
register = template.Library()
from pprint import pprint

def get_layer_download_url(link): # Only one argument.
    return link.get_download_url()
    
register.filter('get_layer_download_url', get_layer_download_url)

