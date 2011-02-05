"""
Tag for returning a list of official sites; currently used for 'Browse Maps' menu dropdown
"""
import logging

from django import template
from django.db import models
from geonode.utils import ConfigMap, DictMixin
from geonode.maps.models import Map



register = template.Library()



#@register.simple_tag
#def officialsites():
#    sites = Map.objects.raw("SELECT * from maps_map where officialurl is not NULL" )
#    logging.info(sites.length())
#    return sites


class OfficialSites(template.Node):
    def __init__(self):
        self.officialsites = Map.objects.raw("SELECT * from maps_map where officialurl is not NULL" )

    def render(self, context):
        context['official_sites'] = Map.objects.raw("SELECT * from maps_map where officialurl is not NULL" )
        return ''



@register.tag('official_sites')
def do_officialsites(parser, token):
    return OfficialSites()