from geonode import settings
from django.contrib.auth.forms import AuthenticationForm
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.http import HttpResponse
import simplejson
from geonode.maps.models import MapLayer
from geonode.gazetteer.utils import getGazetteerResults, getGazetteerEntry, getExternalServiceResults

__author__ = 'mbertrand'
from piston.handler import BaseHandler
from piston.utils import rc, throttle
from django.utils.translation import ugettext as _

class DjangoAuthentication(object):
    """
    Django authentication for piston
    """
    request = None
    errors = None

    def is_authenticated(self, request):
        """
        if user is_authenticated: return True
        else try to autenticate with django and return true/false dependent of
        result
        """
        self.request = request

        # is authenticated
        if self.request.user.is_authenticated():
            return True

        # not authenticated, call authentication form
        f = AuthenticationForm(data={
            'username': self.request.POST.get('username',''),
            'password': self.request.POST.get('password',''),
            })

        # if authenticated log the user in.
        if f.is_valid():

            auth_login(self.request,f.get_user())
            # this ** should ** return true
            return self.request.user.is_authenticated()

        else:
            # fail to auth, save form errors
            self.errors = f.errors
            return False

    def challenge(self):
        """
        `challenge`: In cases where `is_authenticated` returns
        False, the result of this method will be returned.
        This will usually be a `HttpResponse` object with
        some kind of challenge headers and 401 code on it.
        """
        resp = { 'error': _('Authentication needed'), 'msgs': self.errors }
        return HttpResponse(simplejson.dumps(
            resp, cls=DateTimeAwareJSONEncoder,
            ensure_ascii=False, indent=4),
            status=401,mimetype="application/json")



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





