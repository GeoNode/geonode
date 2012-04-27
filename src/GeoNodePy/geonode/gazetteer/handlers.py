from geonode import settings
from geonode.maps.models import MapLayer
from geonode.gazetteer.utils import getGazetteerResults, getGazetteerEntry, getExternalServiceResults

__author__ = 'mbertrand'
import re
from piston.handler import BaseHandler
from piston.utils import rc, throttle
from geopy import geocoders

class DjangoAuthentication(object):
    """
    Django authentication.
    """
    def __init__(self):
        self.request = None

    def is_authenticated(self, request):
        """
        This method call the `is_authenticated` method of django
        User in django.contrib.auth.models.

        `is_authenticated`: Will be called when checking for
        authentication. It returns True if the user is authenticated
        False otherwise.
        """
        self.request = request
        return request.user.is_authenticated()



class PlaceNameHandler(BaseHandler):
    allowed_methods = ('GET')
    #fields = ('layerName', ('latitude', 'longitude'), 'source')

    @classmethod
    def read(self, request, place_name, map = None, layer = None, start_date = None, end_date = None, project=None, services=None):
        if place_name.isdigit():
            posts = getGazetteerEntry(place_name)
        else:
            posts = getGazetteerResults(place_name, map, layer, start_date, end_date, project)
        if services is not None:
            posts.extend(getExternalServiceResults(place_name,services))
        return posts

    @classmethod
    def write(self, request, place_name, map = None, layer = None, start_date = None, end_date = None, project=None, service=None):
        return None




