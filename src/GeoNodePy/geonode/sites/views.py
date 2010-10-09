# Create your views here.
from geonode.core.models import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.maps.models import Map, Layer, LayerCategory, MapLayer, Contact, ContactRole,Role, get_csw
from geonode.maps.gs_helpers import fixup_style
from geonode.sites.models import UserSite, UserSiteLayer
from geonode import geonetwork
import geoserver
from geoserver.resource import FeatureType, Coverage
import base64
from django import forms
from django.contrib.auth import authenticate, get_backends as get_auth_backends
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from django.template import RequestContext, loader
from django.utils.translation import ugettext as _
import json
import math
import httplib2 
from owslib.csw import CswRecord, namespaces
from owslib.util import nspath
import re
from urllib import urlencode
from urlparse import urlparse
import uuid
import unicodedata
from django.views.decorators.csrf import csrf_exempt, csrf_response_exempt
from django.forms.models import inlineformset_factory
from django.db.models import Q

_user, _password = settings.GEOSERVER_CREDENTIALS

DEFAULT_TITLE = ""
DEFAULT_ABSTRACT = ""

def site(request, site):
    theSite = UserSite.objects.get(urlSuffix = site)
    map = theSite.map

    config = map.viewer_json()
    config.update({"site": theSite.urlSuffix})
    return render_to_response('sites/index.html', RequestContext(request, {
        'config': json.dumps(config),
        'theSite': theSite,
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
        'GEOSERVER_BASE_URL' : settings.GEOSERVER_BASE_URL
    }))

        





