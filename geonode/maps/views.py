from geonode.core.models import AUTHENTICATED_USERS, ANONYMOUS_USERS, CUSTOM_GROUP_USERS
from geonode.maps.models import Map, Layer, MapLayer, Contact, ContactRole, \
     get_csw, LayerCategory, LayerAttribute, MapSnapshot, MapStats, LayerStats, CHARSETS
from geonode.profile.forms import ContactProfileForm
from geoserver.resource import FeatureType, Coverage
import base64
from django import forms
from django.contrib.auth import authenticate, get_backends as get_auth_backends
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from django.template import RequestContext, loader
from django.utils.translation import ugettext as _
from django.utils import simplejson as json
from django.views.generic.simple import direct_to_template
from django.template.defaultfilters import slugify

import math
import httplib2
from owslib.csw import namespaces
from owslib.util import nspath
import re
from urllib import urlencode
from urlparse import urlparse
import unicodedata
from django.db.models import Q
import logging
from geonode.flexidates import FlexiDateFormField
import taggit
from geonode.maps.utils import forward_mercator
from geonode.maps.utils import get_db_store_name
from geonode.maps.owslib_csw import CswRecord
from django.utils.html import escape, strip_tags
from django.forms.models import inlineformset_factory
from django.core.cache import cache
from geonode.maps.forms import LayerCreateForm, GEOMETRY_CHOICES

import itertools
from registration.models import RegistrationProfile
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from datetime import datetime, timedelta
from geonode.maps.gs_helpers import get_sld_for, get_postgis_bbox
from geonode.maps.encode import num_encode, num_decode
from django.db import transaction
import autocomplete_light
from geonode.maps.encode import despam, XssCleaner
from geonode.actions.models import Action

from .forms import EndpointForm

logger = logging.getLogger("geonode.maps.views")

_user, _password = settings.GEOSERVER_CREDENTIALS

DEFAULT_TITLE = ""
DEFAULT_ABSTRACT = ""
DEFAULT_URL = ""

def default_map_config():
    _DEFAULT_MAP_CENTER = forward_mercator(settings.DEFAULT_MAP_CENTER)

    _default_map = Map(
        title=DEFAULT_TITLE,
        abstract=DEFAULT_ABSTRACT,
        projection="EPSG:900913",
        center_x=_DEFAULT_MAP_CENTER[0],
        center_y=_DEFAULT_MAP_CENTER[1],
        zoom=settings.DEFAULT_MAP_ZOOM
    )
    def _baselayer(lyr, order):
        if "args" in lyr:
            lyr["args"][0] = _(lyr["args"][0])
        return MapLayer.objects.from_viewer_config(
            map_model = _default_map,
            layer = lyr,
            source = lyr["source"],
            ordering = order
        )

    DEFAULT_BASE_LAYERS = [_baselayer(lyr, idx) for idx, lyr in enumerate(settings.MAP_BASELAYERS)]
    DEFAULT_MAP_CONFIG = _default_map.viewer_json(None,*DEFAULT_BASE_LAYERS)

    return DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS



def bbox_to_wkt(x0, x1, y0, y1, srid="4326"):
    return 'SRID='+srid+';POLYGON(('+x0+' '+y0+','+x0+' '+y1+','+x1+' '+y1+','+x1+' '+y0+','+x0+' '+y0+'))'


class GazetteerForm(forms.Form):

    project = forms.CharField(label=_('Custom Gazetteer Name (Project Name)'), max_length=128, required=False)
    startDate = forms.ModelChoiceField(label = _("Start depict-date field"),
        required=False,
        queryset = LayerAttribute.objects.none())

    startDateFormat = forms.CharField(label=_("Date format"), max_length=256, required=False)

    endDate = forms.ModelChoiceField(label = _("End depict-date field"),
        required=False,
        queryset = LayerAttribute.objects.none())

    endDateFormat = forms.CharField(label=_("Date format"), max_length=256, required=False)


class LayerContactForm(forms.Form):
    poc = forms.ModelChoiceField(empty_label = _("Person outside WorldMap (fill form)"),
        label = "*" + _("Point Of Contact"), required=False,
        queryset = Contact.objects.exclude(user=None),
        widget=autocomplete_light.ChoiceWidget('ContactAutocomplete'))

    metadata_author = forms.ModelChoiceField(empty_label = _("Person outside WorldMap (fill form)"),
        label = _("Metadata Author"), required=False,
        queryset = Contact.objects.exclude(user=None),
        widget=autocomplete_light.ChoiceWidget('ContactAutocomplete'))

    class Meta:
        model = Contact


class LayerForm(forms.ModelForm):
    from geonode.maps.models import CONSTRAINT_OPTIONS
    CONSTRAINT_HELP = _('''<p>Please choose the appropriate type of restriction (if any) for the use of your data.
    Then use the "Constraints Other" form below to provide any necessary details.</p>
    <p>
    Public Domain Dedication and License<br />
    http://opendatacommons.org/licenses/pddl/
    </p>
    <p>
    Attribution License (ODC-By)<br />
    http://opendatacommons.org/licenses/by/
    </p>
    <p>
    Open Database License (ODC-ODbL)<br />
    http://opendatacommons.org/licenses/odbl/
    </p>
    <p>
    CC-BY-SA<br />
    http://creativecommons.org/licenses/by-sa/2.0/
    ''')

    map_id = forms.CharField(widget=forms.HiddenInput(), initial='', required=False)
    date = forms.DateTimeField(label='*' + (_('Date')), widget=forms.SplitDateTimeWidget)
    date.widget.widgets[0].attrs = {"class":"date"}
    date.widget.widgets[1].attrs = {"class":"time"}
    temporal_extent_start = FlexiDateFormField(required=False,label= _('Temporal Extent Start Date'))
    temporal_extent_end = FlexiDateFormField(required=False,label= _('Temporal Extent End Date'))
    title = forms.CharField(label = '*' + _('Title'), max_length=255)
    abstract = forms.CharField(label = '*' + _('Abstract'), widget=forms.Textarea(attrs={'cols': 60}))
    constraints_use = forms.ChoiceField(label= _('Contraints'), choices=CONSTRAINT_OPTIONS,
                                        help_text=CONSTRAINT_HELP)
    keywords = taggit.forms.TagField(required=False)
    class Meta:
        model = Layer
        exclude = ('owner', 'contacts','workspace', 'store', 'name', 'uuid', 'storeType', 'typename', 'topic_category', 'bbox', 'llbbox', 'srs', 'geographic_bounding_box', 'in_gazetteer', 'gazetteer_project' ) #, 'topic_category'

class RoleForm(forms.ModelForm):
    class Meta:
        model = ContactRole
        exclude = ('contact', 'layer')

class PocForm(forms.Form):
    contact = forms.ModelChoiceField(label = _("New point of contact"),
                                     queryset = Contact.objects.exclude(user=None))


class MapForm(forms.ModelForm):
    keywords = taggit.forms.TagField(required=False)
    title = forms.CharField()
    abstract = forms.CharField(widget=forms.Textarea(attrs={'cols': 40, 'rows': 10}), required=False)
    content = forms.CharField(widget=forms.Textarea(attrs={'cols': 60, 'rows': 10, 'id':'mapdescription'}), required=False)

    class Meta:
        model = Map
        exclude = ('contact', 'zoom', 'projection', 'center_x', 'center_y', 'owner', 'officialurl', 'urlsuffix', 'keywords', 'use_custom_template', 'group_params')



MAP_LEV_NAMES = {
    Map.LEVEL_NONE  : _('No Permissions'),
    Map.LEVEL_READ  : _('Read Only'),
    Map.LEVEL_WRITE : _('Read/Write'),
    Map.LEVEL_ADMIN : _('Administrative')
}
LAYER_LEV_NAMES = {
    Layer.LEVEL_NONE  : _('No Permissions'),
    Layer.LEVEL_READ  : _('Read Only'),
    Layer.LEVEL_WRITE : _('Read/Write'),
    Layer.LEVEL_ADMIN : _('Administrative')
}

def maps(request): # , mapid=None):
    if request.method == 'GET':
        return render_to_response('maps.html', RequestContext(request))
    elif request.method == 'POST':
        if not request.user.is_authenticated():
            return HttpResponse(
                'You must be logged in to save new maps',
                mimetype="text/plain",
                status=401
            )
        else:
            # create a new map
            map_obj = Map(owner=request.user, zoom=0, center_x=0, center_y=0)
            map_obj.save()
            map_obj.set_default_permissions()
            try:
                map_obj.update_from_viewer(request.raw_post_data)
                MapSnapshot.objects.create(config=clean_config(request.raw_post_data),map=map_obj,user=request.user)

                # audit action
                username = request.user.get_profile().username()
                action = Action(
                    action_type='map_create',
                    description='User %s created map titled "%s"' % (username, map_obj.title),
                    args=map_obj.id,
                )
                action.save()

            except ValueError, e:
                return HttpResponse(str(e), status=400)
            else:
                response = HttpResponse('', status=201)
                response['Location'] = map_obj.officialurl if map_obj.officialurl else (map_obj.urlsuffix if map_obj.urlsuffix else map_obj.id)
                transaction.commit()
                return response


def mapJSON(request, mapid):
    if request.method == 'GET':
        map_obj = get_object_or_404(Map,pk=mapid)
        if not request.user.has_perm('maps.view_map', obj=map_obj):
            return HttpResponse(loader.render_to_string('401.html',
                RequestContext(request, {})), status=401)
    	return HttpResponse(json.dumps(map_obj.viewer_json(request.user)))
    elif request.method == 'PUT':
        if not request.user.is_authenticated():
            return HttpResponse(
                _("You must be logged in to save this map"),
                status=401,
                mimetype="text/plain"
            )
        map_obj = get_object_or_404(Map, pk=mapid)
        if not request.user.has_perm('maps.change_map', obj=map_obj):
            return HttpResponse(_("You are not allowed to modify this map."), status=403)
        try:
            map_obj.update_from_viewer(request.raw_post_data)
            MapSnapshot.objects.create(config=clean_config(request.raw_post_data),map=Map.objects.get(id=map_obj.id),user=request.user)
            return HttpResponse(
                _("Map successfully updated."),
                mimetype="text/plain",
                status=204
            )
        except Exception, e:
            return HttpResponse(
                _("The server could not understand the request.") + str(e),
                mimetype="text/plain",
                status=400
            )

def newmap_config(request):
    '''
    View that creates a new map.

    If the query argument 'copy' is given, the inital map is
    a copy of the map with the id specified, otherwise the
    default map configuration is used.  If copy is specified
    and the map specified does not exist a 404 is returned.
    '''
    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config()

    if request.method == 'GET' and 'copy' in request.GET:
        mapid = request.GET['copy']
        map_obj = get_object_or_404(Map,pk=mapid)

        if not request.user.has_perm('maps.view_map', obj=map_obj):
            return HttpResponse(loader.render_to_string('401.html',
                RequestContext(request, {'error_message':
                    _("You are not permitted to view or copy this map.")})), status=401)

        map_obj.abstract = DEFAULT_ABSTRACT
        map_obj.title = DEFAULT_TITLE
        map_obj.urlsuffix = DEFAULT_URL
        if request.user.is_authenticated(): map_obj.owner = request.user
        config = map_obj.viewer_json(request.user)
        config['edit_map'] = True
        if 'id' in config:
            del config['id']
    else:
        if request.method == 'GET':
            params = request.GET
        elif request.method == 'POST':
            params = request.POST
        else:
            return HttpResponse(status=405)

        if 'layer' in params:
            map_obj = Map(projection="EPSG:900913")
            layers, groups, bbox = additional_layers(request,map_obj, params.getlist('layer'))

            #print 'layers', layers
            #print 'type: ', type(layers[0])
            if bbox is not None:
                minx, miny, maxx, maxy = [float(c) for c in bbox]
                x = (minx + maxx) / 2
                y = (miny + maxy) / 2

                center = forward_mercator((x, y))
                if center[1] == float('-inf'):
                    center[1] = 0

                if maxx == minx:
                    width_zoom = 15
                else:
                    width_zoom = math.log(360 / (maxx - minx), 2)
                if maxy == miny:
                    height_zoom = 15
                else:
                    height_zoom = math.log(360 / (maxy - miny), 2)

                map_obj.center_x = center[0]
                map_obj.center_y = center[1]
                map_obj.zoom = math.ceil(min(width_zoom, height_zoom))

            config = map_obj.viewer_json(request.user, *(DEFAULT_BASE_LAYERS + layers))
            config['map']['groups'] = []
            for group in groups:
                if group not in json.dumps(config['map']['groups']):
                    config['map']['groups'].append({"expanded":"true", "group":group})

            config['fromLayer'] = True
        else:
            config = DEFAULT_MAP_CONFIG
        config['topic_categories'] = category_list()
        config['edit_map'] = True
    return json.dumps(config)

def newmap(request):
    config = newmap_config(request)
    if isinstance(config, HttpResponse):
        return config
    else:
        return render_to_response('maps/view.html', RequestContext(request, {
        'config': config,
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
        'GEOSERVER_BASE_URL' : settings.GEOSERVER_BASE_URL,
        'GEONETWORK_BASE_URL' : settings.GEONETWORK_BASE_URL,
        'maptitle': settings.SITENAME,
        'DB_DATASTORE' : settings.DB_DATASTORE
    }))

def newmapJSON(request):
    config = newmap_config(request)
    if isinstance(config, HttpResponse):
        return config
    else:
        return HttpResponse(config)

h = httplib2.Http()
h.add_credentials(_user, _password)
h.add_credentials(_user, _password)
_netloc = urlparse(settings.GEOSERVER_BASE_URL).netloc
h.authorizations.append(
    httplib2.BasicAuthentication(
        (_user, _password),
        _netloc,
        settings.GEOSERVER_BASE_URL,
        {},
        None,
        None,
        h
    )
)


@login_required
def map_download(request, mapid):
    """
    Download all the layers of a map as a batch
    XXX To do, remove layer status once progress id done
    This should be fix because
    """
    mapObject = get_object_or_404(Map,pk=mapid)
    if not request.user.has_perm('maps.view_map', obj=mapObject):
        return HttpResponse(_('Not Permitted'), status=401)

    map_status = dict()
    if request.method == 'POST':
        url = "%srest/process/batchDownload/launch/" % settings.GEOSERVER_BASE_URL

        def perm_filter(layer):
            return request.user.has_perm('maps.view_layer', obj=layer)

        mapJson = mapObject.json(perm_filter)

        resp, content = h.request(url, 'POST', body=mapJson)

        if resp.status not in (400, 404, 417):
            map_status = json.loads(content)
            request.session["map_status"] = map_status
        else:
            pass # XXX fix

    locked_layers = []
    remote_layers = []
    downloadable_layers = []

    for lyr in mapObject.layer_set.all():
        if lyr.group != "background":
            if not lyr.local():
                remote_layers.append(lyr)
            else:
                ownable_layer = Layer.objects.get(typename=lyr.name)
                if not request.user.has_perm('maps.view_layer', obj=ownable_layer):
                    locked_layers.append(lyr)
                else:
                    downloadable_layers.append(lyr)

    return render_to_response('maps/download.html', RequestContext(request, {
         "map_status" : map_status,
         "map" : mapObject,
         "locked_layers": locked_layers,
         "remote_layers": remote_layers,
         "downloadable_layers": downloadable_layers,
         "geoserver" : settings.GEOSERVER_BASE_URL,
         "site" : settings.SITEURL
    }))


def check_download(request):
    """
    this is an endpoint for monitoring map downloads
    """
    try:
        layer = request.session["map_status"]
        if type(layer) == dict:
            url = "%srest/process/batchDownload/status/%s" % (settings.GEOSERVER_BASE_URL,layer["id"])
            resp,content = h.request(url,'GET')
            status= resp.status
            if resp.status == 400:
                return HttpResponse(content="Something went wrong",status=status)
        else:
            content = "Something Went wrong"
            status  = 400
    except ValueError:
        # TODO: Is there any useful context we could include in this log?
        logger.warn("User tried to check status, but has no download in progress.")
    return HttpResponse(content=content,status=status)


def batch_layer_download(request):
    """
    batch download a set of layers

    POST - begin download
    GET?id=<download_id> monitor status
    """

    # currently this just piggy-backs on the map download backend
    # by specifying an ad hoc map that contains all layers requested
    # for download. assumes all layers are hosted locally.
    # status monitoring is handled slightly differently.

    if request.method == 'POST':
        layers = request.POST.getlist("layer")
        layers = Layer.objects.filter(typename__in=list(layers))

        def layer_son(layer):
            return {
                "name" : layer.typename,
                "service" : layer.service_type,
                "metadataURL" : "",
                "serviceURL" : ""
            }

        readme = """This data is provided by GeoNode.

Contents:
"""
        def list_item(lyr):
            return "%s - %s.*" % (lyr.title, lyr.name)

        readme = "\n".join([readme] + [list_item(l) for l in layers])

        fake_map = {
            "map": { "readme": readme },
            "layers" : [layer_son(lyr) for lyr in layers]
        }

        url = "%srest/process/batchDownload/launch/" % settings.GEOSERVER_BASE_URL
        resp, content = h.request(url,'POST',body=json.dumps(fake_map))
        return HttpResponse(content, status=resp.status)


    if request.method == 'GET':
        # essentially, this just proxies back to geoserver
        download_id = request.GET.get('id', None)
        if download_id is None:
            return HttpResponse(status=404)

        url = "%srest/process/batchDownload/status/%s" % (settings.GEOSERVER_BASE_URL, download_id)
        resp,content = h.request(url,'GET')
        return HttpResponse(content, status=resp.status)

def set_layer_permissions(layer, perm_spec, use_email = False):
    if "authenticated" in perm_spec:
        layer.set_gen_level(AUTHENTICATED_USERS, perm_spec['authenticated'])
    if "anonymous" in perm_spec:
        layer.set_gen_level(ANONYMOUS_USERS, perm_spec['anonymous'])
    if "customgroup" in perm_spec:
        layer.set_gen_level(CUSTOM_GROUP_USERS, perm_spec['customgroup'])
    users = [n for (n, p) in perm_spec['users']]
    if use_email:
        layer.get_user_levels().exclude(user__email__in = users + [layer.owner]).delete()
        for useremail, level in perm_spec['users']:
            user_obj = None
            try:
                user_obj = User.objects.get(email=useremail)
            except User.DoesNotExist:
                try:
                    user_obj = _create_new_user(useremail, layer.title, reverse('geonode.maps.views.layer_detail', args=(layer.typename,)), layer.owner_id)
                except:
                    logger.info("Could not create new user with email address of %s" % useremail)
            if user_obj:
                layer.set_user_level(user_obj, level)
    else:
        layer.get_user_levels().exclude(user__username__in = users + [layer.owner]).delete()
        for username, level in perm_spec['users']:
            user = User.objects.get(username=username)
            layer.set_user_level(user, level)
    # Always make sure owner keeps control
    if layer.owner is not None:
        layer.set_user_level(layer.owner, layer.LEVEL_ADMIN)

def set_map_permissions(m, perm_spec, use_email = False):
    if "authenticated" in perm_spec:
        m.set_gen_level(AUTHENTICATED_USERS, perm_spec['authenticated'])
    if "anonymous" in perm_spec:
        m.set_gen_level(ANONYMOUS_USERS, perm_spec['anonymous'])
    if "customgroup" in perm_spec:
        m.set_gen_level(CUSTOM_GROUP_USERS, perm_spec['customgroup'])
    users = [n for (n, p) in perm_spec['users']]
    if use_email:
        m.get_user_levels().exclude(user__email__in = users + [m.owner]).delete()
        for useremail, level in perm_spec['users']:
            user_obj = None
            try:
                user_obj = User.objects.get(email=useremail)
            except User.DoesNotExist:
                try:
                    user_obj = _create_new_user(useremail, m.title, reverse('geonode.maps.views.view', args=[m.id]), m.owner_id)
                except:
                    logger.info("Could not create new user with email address of %s" % useremail)
            if user_obj:
                m.set_user_level(user_obj, level)
    else:
        m.get_user_levels().exclude(user__username__in = users + [m.owner]).delete()
        for username, level in perm_spec['users']:
            user = User.objects.get(username=username)
            m.set_user_level(user, level)


def ajax_layer_permissions(request, layername, use_email=False):
    layer = get_object_or_404(Layer, typename=layername)

    if not request.method == 'POST':
        return HttpResponse(
            _('You must use POST for editing layer permissions'),
            status=405,
            mimetype='text/plain'
        )

    if not request.user.has_perm("maps.change_layer_permissions", obj=layer):
        return HttpResponse(
            _('You are not allowed to change permissions for this layer'),
            status=401,
            mimetype='text/plain'
        )

    permission_spec = json.loads(request.raw_post_data)
    set_layer_permissions(layer, permission_spec, use_email)

    return HttpResponse(
        "Permissions updated",
        status=200,
        mimetype='text/plain'
    )

def ajax_map_permissions(request, mapid, use_email=False):
    map_obj = get_object_or_404(Map, pk=mapid)

    if not request.user.has_perm("maps.change_map_permissions", obj=map_obj):
        return HttpResponse(
            _('You are not allowed to change permissions for this map'),
            status=401,
            mimetype='text/plain'
        )

    if not request.method == 'POST':
        return HttpResponse(
            'You must use POST for editing map permissions',
            status=405,
            mimetype='text/plain'
        )

    spec = json.loads(request.raw_post_data)
    set_map_permissions(map_obj, spec, use_email)

    # _perms = {
    #     Layer.LEVEL_READ: Map.LEVEL_READ,
    #     Layer.LEVEL_WRITE: Map.LEVEL_WRITE,
    #     Layer.LEVEL_ADMIN: Map.LEVEL_ADMIN,
    # }

    # def perms(x):
    #     return _perms.get(x, Map.LEVEL_NONE)

    # if "anonymous" in spec:
    #     map.set_gen_level(ANONYMOUS_USERS, perms(spec['anonymous']))
    # if "authenticated" in spec:
    #     map.set_gen_level(AUTHENTICATED_USERS, perms(spec['authenticated']))
    # users = [n for (n, p) in spec["users"]]
    # map.get_user_levels().exclude(user__username__in = users + [map.owner]).delete()
    # for username, level in spec['users']:
    #     user = User.objects.get(username = username)
    #     map.set_user_level(user, perms(level))

    return HttpResponse(
        "Permissions updated",
        status=200,
        mimetype='text/plain'
    )

@login_required
def deletemap(request, mapid):
    ''' Delete a map, and its constituent layers. '''
    map_obj = get_object_or_404(Map,pk=mapid)

    if not request.user.has_perm('maps.delete_map', obj=map_obj):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(request, {'error_message':
                _("You are not permitted to delete this map.")})), status=401)

    if request.method == 'GET':
        return render_to_response("maps/map_remove.html", RequestContext(request, {
            "map": map_obj,
            'urlsuffix': get_suffix_if_custom(map_obj)
        }))
    elif request.method == 'POST':
        map_id = map_obj.id
        map_title = map_obj.title
        username = request.user.get_profile().username()
        layers = map_obj.layer_set.all()
        for layer in layers:
            layer.delete()
        map_obj.delete()

        # audit action
        action = Action(
            action_type='map_delete',
            description='User %s deleted map titled "%s"' % (username, map_title),
            args=map_id,
        )
        action.save()

        return HttpResponseRedirect(request.user.get_profile().get_absolute_url())

def mapdetail(request,mapid):
    '''
    The view that show details of each map
    '''
    map_obj = get_object_or_404(Map,pk=mapid)
    if not request.user.has_perm('maps.view_map', obj=map_obj):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(request, {'error_message':
                _("You are not allowed to view this map.")})), status=401)
    config = map_obj.viewer_json(request.user)
    config = json.dumps(config)
    layers = MapLayer.objects.filter(map=map_obj.id)
    mapstats, created = MapStats.objects.get_or_create(map=map_obj.id)
    return render_to_response("maps/mapinfo.html", RequestContext(request, {
        'config': config,
        'map': map_obj,
        'layers': layers,
        'mapstats': mapstats,
        'permissions_json': _perms_info_email_json(map_obj, MAP_LEV_NAMES),
        'customGroup': settings.CUSTOM_GROUP_NAME if settings.USE_CUSTOM_ORG_AUTHORIZATION else '',
        'urlsuffix':get_suffix_if_custom(map_obj)
    }))


@login_required
def describemap(request, mapid):
    '''
    The view that displays a form for
    editing map metadata
    '''
    map_obj = get_object_or_404(Map,pk=mapid)
    if not request.user.has_perm('maps.change_map', obj=map_obj):
        return HttpResponse(loader.render_to_string('401.html',
                            RequestContext(request, {'error_message':
                            _("You are not allowed to modify this map's metadata.")})),
                            status=401)

    if request.method == "POST":
        # Change metadata, return to map info page
        map_form = MapForm(request.POST, instance=map_obj, prefix="map")

        if map_form.is_valid():
            new_title = strip_tags(map_form.cleaned_data["title"])
            new_abstract = strip_tags(map_form.cleaned_data["abstract"])
            map_obj = map_form.save(commit=False)
            if map_form.cleaned_data["keywords"]:
                map_obj.keywords.clear()
                map_obj.keywords.add(*map_form.cleaned_data["keywords"])
            else:
                map_obj.keywords.clear()
            map_obj.title = new_title
            map_obj.abstract = new_abstract
            map_obj.save()

            return HttpResponseRedirect(reverse('geonode.maps.views.map_controller', args=(map_obj.id,)))
    else:
        # Show form
        map_form = MapForm(instance=map_obj, prefix="map")

    return render_to_response("maps/map_describe.html", RequestContext(request, {
        "map": map_obj,
        "map_form": map_form,
        "urlsuffix": get_suffix_if_custom(map_obj)
    }))

def map_controller(request, mapid):
    '''
    main view for map resources, dispatches to correct
    view based on method and query args.
    '''
    if mapid.isdigit():
        map_obj = Map.objects.get(pk=mapid)
    else:
        map_obj = Map.objects.get(urlsuffix=mapid)
    if 'removenow' in request.GET:
        return deletemapnow(request, map_obj.id)
    elif 'remove' in request.GET:
        return deletemap(request, map_obj.id)
    elif 'describe' in request.GET:
        return describemap(request, map_obj.id)
    else:
        return mapdetail(request, map_obj.id)


def additional_layers(request, map_obj, layerlist):

    groups = set()
    layers = []
    bbox = None
    for layer_name in layerlist:
        try:
            layer = Layer.objects.get(typename=layer_name)
        except ObjectDoesNotExist:
            # bad layer, skip
            continue

        #layer_bbox = layer.resource.latlon_bbox
        # assert False, str(layer_bbox)
        bbox = layer.llbbox_coords()

        group = layer.topic_category.title if layer.topic_category else "General"
        if group not in groups:
            groups.add(group)

        layers.append(MapLayer(
                    map = map_obj,
                    name = layer.typename,
                    ows_url = settings.GEOSERVER_BASE_URL + "wms",
                    visibility = request.user.has_perm('maps.view_layer', obj=layer),
                    styles='',
                    group=group,
                    source_params = u'{"ptype": "gxp_gnsource"}',
                    layer_params= u'{"tiled":true, "title":" '+ layer.title + '", "format":"image/png","queryable":true}')
                )
    return layers, groups, bbox

def view(request, mapid, snapshot=None):
    """
    The view that returns the map composer opened to
    the map with the given map ID.
    """
    if mapid.isdigit():
        map_obj = get_object_or_404(Map,pk=mapid)
    else:
        map_obj = get_object_or_404(Map,urlsuffix=mapid)
    if not request.user.has_perm('maps.view_map', obj=map_obj):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(request, {'error_message':
                _("You are not allowed to view this map.")})), status=401)


    if 'layer' in request.GET:
        addedlayers, groups, bbox = additional_layers(request,map_obj, request.GET.getlist('layer'))
        config = map_obj.viewer_json(request.user, *addedlayers)
        for group in groups:
            if group not in json.dumps(config['map']['groups']):
                config['map']['groups'].append({"expanded":"true", "group":group})
    elif snapshot is None:
        config = map_obj.viewer_json(request.user)
    else:
        config = snapshot_config(snapshot, map_obj, request.user)

    for layer in config['map']['layers']:
        if 'local' in layer:
            if 'styles' in layer:
                if layer['styles'] is None:
                    logger.info('fixing style for layer %s' % layer['name'])
                    layer['styles'] = ''

    first_visit = True
    if request.session.get('visit' + str(map_obj.id), False):
        first_visit = False
    else:
        request.session['visit' + str(map_obj.id)] = True

    mapstats, created = MapStats.objects.get_or_create(map=map_obj)
    mapstats.visits += 1
    if created or first_visit:
            mapstats.uniques+=1
    mapstats.save()

    #Remember last visited map
    request.session['lastmap'] = map_obj.id
    request.session['lastmapTitle'] = map_obj.title

    config['first_visit'] = first_visit
    config['uid'] = request.user.id
    config['edit_map'] = request.user.has_perm('maps.change_map', obj=map_obj)
    config['topic_categories'] = category_list()

    template_page = 'maps/view.html'
    if map_obj.template_page:
        template_page = map_obj.template_page

    return render_to_response(template_page, RequestContext(request, {
        'config': json.dumps(config),
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
        'GEONETWORK_BASE_URL' : settings.GEONETWORK_BASE_URL,
        'GEOSERVER_BASE_URL' : settings.GEOSERVER_BASE_URL,
        'DB_DATASTORE' : settings.DB_DATASTORE,
        'maptitle': map_obj.title,
        'urlsuffix': get_suffix_if_custom(map_obj),
        'editmap': config['edit_map']
    }))


def tweetview(request):
    map = get_object_or_404(Map,urlsuffix="tweetmap")
    config = map.viewer_json(request.user)

    redirectPage = 'maps/tweetview.html'

    first_visit = True
    if request.session.get('visit' + str(map.id), False):
        first_visit = False
    else:
        request.session['visit' + str(map.id)] = True

    mapstats, created = MapStats.objects.get_or_create(map=map)
    mapstats.visits += 1
    if created or first_visit:
        mapstats.uniques+=1
    mapstats.save()


    #Remember last visited map
    request.session['lastmap'] = map.id
    request.session['lastmapTitle'] = map.title

    config['first_visit'] = first_visit
    config['edit_map'] = request.user.has_perm('maps.change_map', obj=map)

    geops_ip = "standard"
    if "geopsip" in request.GET:
        geops_ip = request.GET["geopsip"]

    try:
        conn = httplib2.Http(timeout=10)
        testUrl = settings.SITEURL  + "tweetserver/" +  geops_ip  + "/?REQUEST%3DGetFeatureInfo%26SQL%3Dselect%20min(time)%2Cmax(time)%20from%20tweets"
        #testUrl = "http://worldmap.harvard.edu"
        resp, content = conn.request(testUrl, 'GET')
        timerange = json.loads(content)
    except:
        timerange = None
        redirectPage = "maps/tweetstartup.html"

    return render_to_response(redirectPage, RequestContext(request, {
        'config': json.dumps(config),
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
        'GEOSERVER_BASE_URL' : settings.GEOSERVER_BASE_URL,
        'maptitle': map.title,
        'GEOPS_IP': geops_ip,
        'urlsuffix': get_suffix_if_custom(map),
        'tweetdownload': request.user.is_authenticated() and request.user.get_profile().is_org_member,
        'min_date': timerange["results"][0]["min"]*1000 if timerange is not None else 0,
        'max_date': timerange["results"][0]["max"]*1000 if timerange is not None else 0
        }))

def embed(request, mapid=None, snapshot=None):
    if mapid is None:
        config = json.loads(newmap_config(request))
    else:
        if mapid.isdigit():
            map_obj = get_object_or_404(Map,pk=mapid)
        else:
            map_obj = get_object_or_404(Map,urlsuffix=mapid)

        if not request.user.has_perm('maps.view_map', obj=map_obj):
            return HttpResponse(_("Not Permitted"), status=401, mimetype="text/plain")
        if snapshot is None:
            config = map_obj.viewer_json(request.user)
        else:
            config = snapshot_config(snapshot, map_obj, request.user)
        config['first_visit'] = False

    return render_to_response('maps/embed.html', RequestContext(request, {
        'config': json.dumps(config)
    }))


def printmap(request, mapid=None, snapshot=None):

    return render_to_response('maps/map_print.html', RequestContext(request, {}))

def data(request):
    return render_to_response('data.html', RequestContext(request, {
        'GEOSERVER_BASE_URL':settings.GEOSERVER_BASE_URL
    }))

def view_js(request, mapid):
    map_obj = Map.objects.get(pk=mapid)
    if not request.user.has_perm('maps.view_map', obj=map_obj):
        return HttpResponse(_("Not Permitted"), status=401, mimetype="text/plain")
    config = map_obj.viewer_json()
    return HttpResponse(json.dumps(config), mimetype="application/javascript")

class LayerDescriptionForm(forms.Form):
    title = forms.CharField(300)
    abstract = forms.CharField(1000, widget=forms.Textarea, required=False)
    keywords = forms.CharField(500, required=False)


@login_required
def layer_metadata(request, layername):
    layer = get_object_or_404(Layer, typename=layername)
    if request.user.is_authenticated():
        if not request.user.has_perm('maps.change_layer', obj=layer):
            return HttpResponse(loader.render_to_string('401.html',
                RequestContext(request, {'error_message':
                    _("You are not permitted to modify this layer's metadata")})), status=401)

        topic_category = layer.topic_category
        layerAttSet = inlineformset_factory(Layer, LayerAttribute, extra=0, form=LayerAttributeForm, )

        # hack needed to see if the layer is in Postgres (otherwise no gazetteer):
        # all PostGIS stores starts with wm. There is also a dataverse postgres database
        show_gazetteer_form = settings.USE_GAZETTEER
        if layer.store[:2] != 'wm' and layer.store != 'dataverse':
            show_gazetteer_form = False

        fieldTypes = {}
        attributeOptions = layer.attribute_set.filter(attribute_type__in=['xsd:dateTime','xsd:date','xsd:int','xsd:string','xsd:bigint', 'xsd:double'])
        for option in attributeOptions:
            try:
                fieldTypes[option.id] = option.attribute_type
            except Exception, e:
                logger.info("Could not get type for %s", option)

        if request.method == "GET":
            layer_form = LayerForm(instance=layer, prefix="layer")
            category_form = LayerCategoryForm(prefix="category_choice_field", initial=topic_category.id if topic_category else None)


            #layer_form.fields["topic_category"].initial = topic_category
            if "map" in request.GET:
                layer_form.fields["map_id"].initial = request.GET["map"]
            attribute_form = layerAttSet(instance=layer, prefix="layer_attribute_set", queryset=LayerAttribute.objects.order_by('display_order'))
            startAttributeQuerySet = LayerAttribute.objects.filter(layer=layer).filter(is_gaz_start_date=True)
            endAttributeQuerySet = LayerAttribute.objects.filter(layer=layer).filter(is_gaz_end_date=True)
            gazetteer_form = GazetteerForm()


            gazetteer_form.fields['startDate'].queryset = gazetteer_form.fields['endDate'].queryset = attributeOptions
            if gazetteer_form.fields['startDate'].queryset.count() == 0:
                gazetteer_form.fields['startDate'].empty_label = gazetteer_form.fields['endDate'].empty_label = _('No date fields available')
            gazetteer_form.fields['project'].initial = layer.gazetteer_project
            if startAttributeQuerySet.exists():
                gazetteer_form.fields['startDate'].initial = startAttributeQuerySet[0].id
                gazetteer_form.fields['startDateFormat'].initial = startAttributeQuerySet[0].date_format
            if endAttributeQuerySet.exists():
                gazetteer_form.fields['endDate'].initial = endAttributeQuerySet[0].id
                gazetteer_form.fields['endDateFormat'].initial = endAttributeQuerySet[0].date_format

            tab = None
            if "tab" in request.GET:
                tab = request.GET["tab"]


        if request.method == "POST":
            layer_form = LayerForm(request.POST, instance=layer, prefix="layer")
            category_form = LayerCategoryForm(request.POST, prefix="category_choice_field")
            attribute_form = layerAttSet(request.POST, instance=layer, prefix="layer_attribute_set", queryset=LayerAttribute.objects.order_by('display_order'))
            gazetteer_form = GazetteerForm(request.POST)
            gazetteer_form.fields['startDate'].queryset = gazetteer_form.fields['endDate'].queryset = layer.attribute_set

            if "tab" in request.POST:
                tab = request.POST["tab"]

            if layer_form.is_valid() and category_form.is_valid() and (
                    not settings.USE_GAZETTEER or gazetteer_form.is_valid()):

                new_category = LayerCategory.objects.get(id=category_form.cleaned_data['category_choice_field'])

                if attribute_form.is_valid():
                    for form in attribute_form.cleaned_data:
                        la = LayerAttribute.objects.get(id=int(form['id'].id))
                        la.attribute_label = form["attribute_label"]
                        la.searchable = form["searchable"]
                        la.visible = form["visible"]
                        la.display_order = form["display_order"]
                        if settings.USE_GAZETTEER and gazetteer_form.is_valid():
                            la.in_gazetteer = form["in_gazetteer"]
                            la.is_gaz_start_date = (la == gazetteer_form.cleaned_data["startDate"])
                            la.is_gaz_end_date = (la == gazetteer_form.cleaned_data["endDate"])
                            if la.is_gaz_start_date:
                                la.date_format = gazetteer_form.cleaned_data["startDateFormat"].strip() \
                                if len(gazetteer_form.cleaned_data["startDateFormat"]) > 0 else None
                            elif la.is_gaz_end_date:
                                la.date_format = gazetteer_form.cleaned_data["endDateFormat"].strip() \
                                if len(gazetteer_form.cleaned_data["endDateFormat"]) > 0 else None

                        la.save()
                    cache.delete('layer_searchfields_' + layer.typename)
                    logger.debug("Deleted cache for layer_searchfields_" + layer.typename)

                mapid = layer_form.cleaned_data['map_id']
                new_keywords = layer_form.cleaned_data['keywords']

                the_layer = layer_form.save(commit=False)
                x = XssCleaner()
                the_layer.abstract = despam(x.strip(layer_form.cleaned_data["abstract"]))
                the_layer.topic_category = new_category
                the_layer.keywords.clear()
                the_layer.keywords.add(*new_keywords)

                if settings.USE_GAZETTEER and gazetteer_form.is_valid():
                    the_layer.in_gazetteer = "gazetteer_include" in request.POST
                    if the_layer.in_gazetteer:
                        the_layer.gazetteer_project = gazetteer_form.cleaned_data["project"]
                the_layer.save()
                the_layer.save_to_geonetwork()

                if settings.USE_GAZETTEER and show_gazetteer_form:
                    if settings.USE_QUEUE:
                        the_layer.queue_gazetteer_update()
                    else:
                        the_layer.update_gazetteer()

                if request.is_ajax():
                    return HttpResponse('success', status=200)
                elif mapid != '' and str(mapid).lower() != 'new':
                    logger.debug("adding layer to map [%s]", str(mapid))
                    maplayer = MapLayer.objects.create(map=Map.objects.get(id=mapid),
                        name = layer.typename,
                        group = layer.topic_category.title if layer.topic_category else 'General',
                        layer_params = '{"selected":true, "title": "' + layer.title + '"}',
                        source_params = '{"ptype": "gxp_gnsource"}',
                        ows_url = settings.GEOSERVER_BASE_URL + "wms",
                        visibility = True,
                        stack_order = MapLayer.objects.filter(id=mapid).count()
                    )
                    maplayer.save()
                    return HttpResponseRedirect("/maps/" + mapid)
                else:
                    if str(mapid) == "new":
                        return HttpResponseRedirect("/maps/new?layer" + layer.typename)
                    else:
                        return HttpResponseRedirect("/data/" + layer.typename)

        #Deal with a form submission via ajax
        if request.method == 'POST' and (not layer_form.is_valid() or not category_form.is_valid()) and request.is_ajax():
                data = render_to_response("maps/layer_describe_tab.html", RequestContext(request, {
                "layer": layer,
                "layer_form": layer_form,
                "attribute_form": attribute_form,
                "category_form" : category_form,
                "gazetteer_form": gazetteer_form,
                "show_gazetteer_options": show_gazetteer_form,
                "lastmap" : request.session.get("lastmap"),
                "lastmapTitle" : request.session.get("lastmapTitle"),
                "tab" : tab,
                "datatypes" : json.dumps(fieldTypes)
                }))
                return HttpResponse(data, status=412)

        #Display the view in a panel tab
        if 'tab' in request.GET:
            return render_to_response("maps/layer_describe_tab.html", RequestContext(request, {
            "layer": layer,
            "layer_form": layer_form,
            "attribute_form": attribute_form,
            "category_form" : category_form,
            "gazetteer_form": gazetteer_form,
            "show_gazetteer_options": show_gazetteer_form,
            "lastmap" : request.session.get("lastmap"),
            "lastmapTitle" : request.session.get("lastmapTitle"),
            "tab" : tab,
            "datatypes" : json.dumps(fieldTypes)
        }))

        #Display the view on a regular page
        return render_to_response("maps/layer_describe.html", RequestContext(request, {
            "layer": layer,
            "layer_form": layer_form,
            "attribute_form": attribute_form,
            "category_form" : category_form,
            "gazetteer_form": gazetteer_form,
            "show_gazetteer_options": show_gazetteer_form,
            "lastmap" : request.session.get("lastmap"),
            "lastmapTitle" : request.session.get("lastmapTitle"),
            "datatypes" : json.dumps(fieldTypes)
        }))
    else:
        return HttpResponse("Not allowed", status=403)

def layer_remove(request, layername):
    layer = get_object_or_404(Layer, typename=layername)
    if request.user.is_authenticated():
        if not request.user.has_perm('maps.delete_layer', obj=layer):
            return HttpResponse(loader.render_to_string('401.html',
                RequestContext(request, {'error_message':
                    _("You are not permitted to delete this layer")})), status=401)

        if (request.method == 'GET'):
            return render_to_response('maps/layer_remove.html',RequestContext(request, {
                "layer": layer,
                "lastmap" : request.session.get("lastmap"),
                "lastmapTitle" : request.session.get("lastmapTitle")
            }))
        if (request.method == 'POST'):
            layer_title = layer.title
            layer_uuid = layer.uuid
            layer.delete()

            # audit action
            username = request.user.get_profile().username()
            action = Action(
                action_type='layer_delete',
                description='User %s deleted layer titled "%s"' % (username, layer_title),
                args=layer_uuid,
            )
            action.save()

            return HttpResponseRedirect(request.user.get_profile().get_absolute_url())
        else:
            return HttpResponse("Not allowed",status=403)
    else:
        return HttpResponse("Not allowed",status=403)

def layer_style(request, layername):
    layer = get_object_or_404(Layer, typename=layername)
    if request.user.is_authenticated():
        if not request.user.has_perm('maps.change_layer', obj=layer):
            return HttpResponse(loader.render_to_string('401.html',
                RequestContext(request, {'error_message':
                    _("You are not permitted to modify this layer")})), status=401)

        if (request.method == 'POST'):
            style_name = request.POST.get('defaultStyle')

            # would be nice to implement
            # better handling of default style switching
            # in layer model or deeper (gsconfig.py, REST API)

            old_default = layer.default_style
            if old_default.name == style_name:
                return HttpResponse("Default style for %s remains %s" % (layer.name, style_name), status=200)

            # This code assumes without checking
            # that the new default style name is included
            # in the list of possible styles.

            new_style = (style for style in layer.styles if style.name == style_name).next()

            layer.default_style = new_style
            layer.styles = [s for s in layer.styles if s.name != style_name] + [old_default]
            layer.save()
            return HttpResponse("Default style for %s changed to %s" % (layer.name, style_name),status=200)
        else:
            return HttpResponse("Not allowed",status=403)
    else:
        return HttpResponse("Not allowed",status=403)

def layer_detail(request, layername):
    layer = get_object_or_404(Layer, typename=layername)
    if not request.user.has_perm('maps.view_layer', obj=layer):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(request, {'error_message':
                _("You are not permitted to view this layer")})), status=401)

    print '-' * 40
    print '\nlayer.typename', layer.typename
    print 'settings.GEOSERVER_BASE_URL', settings.GEOSERVER_BASE_URL
    print 'layer.default_style.name', layer.default_style.name
    print 'layer.title', layer.title
    print 'layer.attribute_config()', layer.attribute_config(), '\n'
    print '-' * 40
    maplayer = MapLayer(
        name = layer.typename,
        styles=[layer.default_style.name],
        source_params = '{"ptype": "gxp_gnsource"}',
        ows_url = settings.GEOSERVER_BASE_URL + "wms",
        layer_params= '{"tiled":true, "local":true, "title":" '+ layer.title + '", ' + json.dumps(layer.attribute_config()) + '}')

    # center/zoom don't matter; the viewer will center on the layer bounds
    map_obj = Map(projection="EPSG:900913")
    DEFAULT_BASE_LAYERS = default_map_config()[1]

    layerstats,created = LayerStats.objects.get_or_create(layer=layer)

    added_layers = (DEFAULT_BASE_LAYERS + [maplayer])
    viewer = json.dumps(map_obj.viewer_json(request.user, * added_layers))

    return render_to_response('maps/layer.html', RequestContext(request, {
        "layer": layer,
        "layerstats": layerstats,
        "viewer": viewer,
        "permissions_json": _perms_info_email_json(layer, LAYER_LEV_NAMES),
        "customGroup": settings.CUSTOM_GROUP_NAME if settings.USE_CUSTOM_ORG_AUTHORIZATION else '',
        "GEOSERVER_BASE_URL": settings.GEOSERVER_BASE_URL,
        "lastmap" : request.session.get("lastmap"),
        "lastmapTitle" : request.session.get("lastmapTitle")
    }))


GENERIC_UPLOAD_ERROR = _("There was an error while attempting to upload your data. \
Please try again, or contact and administrator if the problem continues.")

@login_required
def upload_layer(request):
    if request.method == 'GET':
            if 'map' in request.GET:
                mapid = request.GET['map']
                map = get_object_or_404(Map,pk=mapid)
                return render_to_response('maps/layer_upload.html',
                                  RequestContext(request, {'map':map, 'charsets': CHARSETS, 'customGroup': settings.CUSTOM_GROUP_NAME if settings.USE_CUSTOM_ORG_AUTHORIZATION else ''}))
            else: #this is a tabbed panel request if no map id provided
                return render_to_response('maps/layer_upload_tab.html',
                                  RequestContext(request, {'charsets': CHARSETS}))
    elif request.method == 'POST':
        from geonode.maps.forms import WorldMapLayerUploadForm
        from geonode.maps.utils import save
        from django.utils.html import escape
        import os, shutil
        form = WorldMapLayerUploadForm(request.POST, request.FILES)
        tempdir = None
        if form.is_valid():
            try:

                tempdir, base_file, sld_file = form.write_files()

                title = form.cleaned_data["layer_title"]

                # Replace dots in filename - GeoServer REST API upload bug
                # and avoid any other invalid characters.
                # Use the title if possible, otherwise default to the filename
                if title is not None and len(title) > 0:
                    name_base = title
                else:
                    name_base, __ = os.path.splitext(form.cleaned_data["base_file"].name)

                name = slugify(name_base.replace(".","_"))


                saved_layer = save(name, base_file, request.user,
                        overwrite = False,
                        abstract = form.cleaned_data["layer_abstract"],
                        title = form.cleaned_data["layer_title"],
                        permissions = form.cleaned_data["permissions"],
                        keywords = form.cleaned_data["layer_keywords"].split(" "),
                        charset = request.POST.get('charset'),
                        sldfile = sld_file
                        )

                # audit action
                username = request.user.get_profile().username()
                action = Action(
                    action_type='layer_upload',
                    description='User %s uploaded layer titled "%s"' % (username, saved_layer.title),
                    args=saved_layer.uuid,
                )
                action.save()

                redirect_to  = reverse('data_metadata', args=[saved_layer.typename])
                if 'mapid' in request.POST and request.POST['mapid'] == 'tab':
                    redirect_to+= "?tab=worldmap_update_panel"
                elif 'mapid' in request.POST and request.POST['mapid'] != '':
                    redirect_to += "?map=" + request.POST['mapid']
                return HttpResponse(json.dumps({
                    "success": True,
                    "redirect_to": redirect_to}))
            except Exception, e:
                logger.error("Unexpected error during upload: %s : %s", name, escape(str(e)))
                return HttpResponse(json.dumps({
                    "success": False,
                    "errormsgs": [_("Unexpected error during upload: ") + escape(str(e))]}))
            finally:
                if tempdir is not None:
                    shutil.rmtree(tempdir)
        else:
            errormsgs = []
            for e in form.errors.values():
                errormsgs.extend([escape(v) for v in e])
            return HttpResponse(json.dumps({ "success": False, "errors": form.errors, "errormsgs": errormsgs}))

@login_required
def layer_replace(request, layername):
    layer = get_object_or_404(Layer, typename=layername)
    if not request.user.has_perm('maps.change_layer', obj=layer):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(request, {'error_message':
                _("You are not permitted to modify this layer")})), status=401)
    if request.method == 'GET':
        cat = Layer.objects.gs_catalog
        store = cat.get_store(layer.store)
        info = cat.get_resource(layer.name,store=store)
        is_featuretype = info.resource_type == FeatureType.resource_type

        return render_to_response('maps/layer_replace.html',
                                  RequestContext(request, {'layer': layer,
                                                           'is_featuretype': is_featuretype,
                                                           'lastmap' : request.session.get("lastmap"),
                                                           'lastmapTitle' : request.session.get("lastmapTitle")}))
    elif request.method == 'POST':
        from geonode.maps.forms import LayerUploadForm
        from geonode.maps.utils import save
        from django.utils.html import escape
        import os, shutil

        form = LayerUploadForm(request.POST, request.FILES)
        tempdir = None

        if form.is_valid():
            try:
                tempdir, base_file, sld_file = form.write_files()
                name, __ = os.path.splitext(form.cleaned_data["base_file"].name)
                saved_layer = save(layer, base_file, request.user, overwrite=True, charset = request.POST.get('charset'), sldfile = sld_file)

                try:
                    #Delete layer attributes if they no longer exist in an updated layer
                    attributes = LayerAttribute.objects.filter(layer=saved_layer)
                    attrNames = layer.attribute_names
                    if attrNames is not None:
                        for la in attributes:
                            lafound = False
                            for field, ftype in attrNames.iteritems():
                                if field == la.attribute:
                                    lafound = True
                            if not lafound:
                                logger.debug("Going to delete [%s] for [%s]", la.attribute, saved_layer.name)
                                la.delete()

                    #Add new layer attributes if they dont already exist
                    if attrNames is not None:
                        logger.debug("Attributes are not None")
                        iter = 1
                        mark_searchable = True
                        for field, ftype in attrNames.iteritems():
                            if re.search('geom|oid|objectid|gid', field, flags=re.I) is None:
                                logger.debug("Field is [%s]", field)
                                las = LayerAttribute.objects.filter(layer=saved_layer, attribute=field)
                                if len(las) == 0:
                                    la = LayerAttribute.objects.create(layer=saved_layer, attribute=field, attribute_label=field.title(), attribute_type=ftype, searchable=(ftype == "xsd:string" and mark_searchable), display_order = iter)
                                    la.save()
                                    if la.searchable:
                                        mark_searchable = False
                                    iter+=1
                    else:
                        logger.debug("No attributes found")

                except Exception, ex:
                    logger.debug("Attributes could not be saved:[%s]", str(ex))
                return HttpResponse(json.dumps({
                    "success": True,
                    "redirect_to": reverse('data_metadata', args=[saved_layer.typename])}))
            except Exception, e:
                try:
                    if len(settings.ADMINS) > 0:
                        send_mail("Upload Error", escape(str(e)), settings.DEFAULT_FROM_EMAIL,[settings.ADMINS[0][1]], fail_silently=True)
                except Exception, f:
                    pass
                logger.exception("Unexpected error during upload.")
                return HttpResponse(json.dumps({
                    "success": False,
                    "errors": [_("Unexpected error during upload: ") + escape(str(e))]}))
            finally:
                if tempdir is not None:
                    shutil.rmtree(tempdir)

        else:
            errors = []
            for e in form.errors.values():
                errors.extend([escape(v) for v in e])
            return HttpResponse(json.dumps({ "success": False, "errors": errors}))


_suffix = re.compile(r"\..*$", re.IGNORECASE) #Accept zipped uploads with more than one extension, ie foo.zip.zip
_xml_unsafe = re.compile(r"(^[^a-zA-Z\._]+)|([^a-zA-Z\._0-9]+)")



def _view_perms_context(obj, level_names):

    ctx =  obj.get_all_level_info()
    def lname(l):
        return level_names.get(l, _("???"))
    ctx[ANONYMOUS_USERS] = lname(ctx.get(ANONYMOUS_USERS, obj.LEVEL_NONE))
    ctx[AUTHENTICATED_USERS] = lname(ctx.get(AUTHENTICATED_USERS, obj.LEVEL_NONE))
    ctx[CUSTOM_GROUP_USERS] = lname(ctx.get(CUSTOM_GROUP_USERS, obj.LEVEL_NONE))

    ulevs = []
    for u, l in ctx['users'].items():
        ulevs.append([u, lname(l)])
    ulevs.sort()
    ctx['users'] = ulevs

    return ctx

def _perms_info(obj, level_names):
    info = obj.get_all_level_info()
    # these are always specified even if none
    info[ANONYMOUS_USERS] = info.get(ANONYMOUS_USERS, obj.LEVEL_NONE)
    info[AUTHENTICATED_USERS] = info.get(AUTHENTICATED_USERS, obj.LEVEL_NONE)
    info[CUSTOM_GROUP_USERS] = info.get(CUSTOM_GROUP_USERS, obj.LEVEL_NONE)
    info['users'] = sorted(info['users'].items())
    info['levels'] = [(i, level_names[i]) for i in obj.permission_levels]
    if hasattr(obj, 'owner') and obj.owner:
        info['owner'] = obj.owner.username
        info['owner_email'] = obj.owner.email
    return info

def _fix_map_perms_for_editor(info):
    perms = {
        Map.LEVEL_READ: Layer.LEVEL_READ,
        Map.LEVEL_WRITE: Layer.LEVEL_WRITE,
        Map.LEVEL_ADMIN: Layer.LEVEL_ADMIN,
    }

    def fix(x): return perms.get(x, "_none")

    info[ANONYMOUS_USERS] = fix(info[ANONYMOUS_USERS])
    info[AUTHENTICATED_USERS] = fix(info[AUTHENTICATED_USERS])
    info[CUSTOM_GROUP_USERS] = fix(info[CUSTOM_GROUP_USERS])
    info['users'] = [(u, fix(level)) for u, level in info['users']]

    return info

INVALID_PERMISSION_MESSAGE = _("Invalid permission level.")
def _handle_perms_edit(request, obj):
    errors = []
    params = request.POST
    valid_pl = obj.permission_levels

    anon_level = params[ANONYMOUS_USERS]
    # validate anonymous level, disallow admin level
    if not anon_level in valid_pl or anon_level == obj.LEVEL_ADMIN:
        errors.append(_("Anonymous Users") + ": " + INVALID_PERMISSION_MESSAGE)

    all_auth_level = params[AUTHENTICATED_USERS]
    if not all_auth_level in valid_pl:
        errors.append(_("Registered Users") + ": " + INVALID_PERMISSION_MESSAGE)

    customgroup_level = params[CUSTOM_GROUP_USERS]
    if not customgroup_level in valid_pl:
        errors.append(_("Custom Group Users") + ": " + INVALID_PERMISSION_MESSAGE)

    kpat = re.compile("^u_(.*)_level$")
    ulevs = {}
    for k, level in params.items():
        m = kpat.match(k)
        if m:
            username = m.groups()[0]
            if not level in valid_pl:
                errors.append(_("User") + " " + username + ": " + INVALID_PERMISSION_MESSAGE)
            else:
                ulevs[username] = level

    if len(errors) == 0:
        obj.set_gen_level(ANONYMOUS_USERS, anon_level)
        obj.set_gen_level(AUTHENTICATED_USERS, all_auth_level)
        obj.set_gen_level(CUSTOM_GROUP_USERS, customgroup_level)

        for username, level in ulevs.items():
            user = User.objects.get(username=username)
            obj.set_user_level(user, level)

    return errors


def _get_basic_auth_info(request):
    """
    grab basic auth info
    """
    meth, auth = request.META['HTTP_AUTHORIZATION'].split()
    if meth.lower() != 'basic':
        raise ValueError
    username, password = base64.b64decode(auth).split(':')
    return username, password

def resolve_user(request):
    user = None
    geoserver = False
    superuser = False
    logger.info("getting user")
    if 'HTTP_AUTHORIZATION' in request.META:
        username, password = _get_basic_auth_info(request)
        logger.info("%s:%s",username,password)
        acl_user = authenticate(username=username, password=password)
        if acl_user:
            user = acl_user.username
            superuser = acl_user.is_superuser
            logger.info("acluser:%s",user)
        elif _get_basic_auth_info(request) == settings.GEOSERVER_CREDENTIALS:
            geoserver = True
            superuser = True
            logger.info("geoserver")
    elif not request.user.is_anonymous():
        user = request.user.username
        superuser = request.user.is_superuser
        logger.info("not anon:%s",user)
    return HttpResponse(json.dumps({
        'user' : user,
        'geoserver' : geoserver,
        'superuser' : superuser
    }))


def layer_acls(request):
    """
    returns json-encoded lists of layer identifiers that
    represent the sets of read-write and read-only layers
    for the currently authenticated user.
    """

    # the layer_acls view supports basic auth, and a special
    # user which represents the geoserver administrator that
    # is not present in django.
    logger.info("WTF is this still used?")
    acl_user = request.user

    if 'HTTP_AUTHORIZATION' in request.META:
        try:
            username, password = _get_basic_auth_info(request)
            acl_user = authenticate(username=username, password=password)

            # Nope, is it the special geoserver user?
            if (acl_user is None and
                username == settings.GEOSERVER_CREDENTIALS[0] and
                password == settings.GEOSERVER_CREDENTIALS[1]):
                # great, tell geoserver it's an admin.
                result = {
                    'rw': [],
                    'ro': [],
                    'name': username,
                    'is_superuser':  True,
                    'is_anonymous': False
                }
                return HttpResponse(json.dumps(result), mimetype="application/json")
        except Exception:
            pass

        if acl_user is None:
            return HttpResponse(_("Bad HTTP Authorization Credentials."),
                status=401,
                mimetype="text/plain")
    all_readable = set()
    all_writable = set()
    for bck in get_auth_backends():
        if hasattr(bck, 'objects_with_perm'):
            all_readable.update(bck.objects_with_perm(acl_user,
                'maps.view_layer',
                Layer))
            all_writable.update(bck.objects_with_perm(acl_user,
                                                      'maps.change_layer',
                                                      Layer))
    read_only = [x for x in all_readable if x not in all_writable]
    read_write = [x for x in all_writable if x in all_readable]

    read_only = [x[0] for x in Layer.objects.filter(id__in=read_only).values_list('typename').all()]
    read_write = [x[0] for x in Layer.objects.filter(id__in=read_write).values_list('typename').all()]

    result = {
        'rw': read_write,
        'ro': read_only,
        'name': acl_user.username,
        'is_superuser':  acl_user.is_superuser,
        'is_anonymous': acl_user.is_anonymous()
    }

    return HttpResponse(json.dumps(result), mimetype="application/json")



def _split_query(query):
    """
    split and strip keywords, preserve space
    separated quoted blocks.
    """

    qq = query.split(' ')
    keywords = []
    accum = None
    for kw in qq:
        if accum is None:
            if kw.startswith('"'):
                accum = kw[1:]
            elif kw:
                keywords.append(kw)
        else:
            accum += ' ' + kw
            if kw.endswith('"'):
                keywords.append(accum[0:-1])
                accum = None
    if accum is not None:
        keywords.append(accum)
    return [kw.strip() for kw in keywords if kw.strip()]



DEFAULT_SEARCH_BATCH_SIZE = 10
MAX_SEARCH_BATCH_SIZE = 25
def metadata_search(request):
    """
    handles a basic search for data using the
    GeoNetwork catalog.

    the search accepts:
    q - general query for keywords across all fields
    start - skip to this point in the results
    limit - max records to return

    for ajax requests, the search returns a json structure
    like this:

    {
    'total': <total result count>,
    'next': <url for next batch if exists>,
    'prev': <url for previous batch if exists>,
    'query_info': {
        'start': <integer indicating where this batch starts>,
        'limit': <integer indicating the batch size used>,
        'q': <keywords used to query>,
    },
    'rows': [
      {
        'name': <typename>,
        'abstract': '...',
        'keywords': ['foo', ...],
        'detail' = <link to geonode detail page>,
        'attribution': {
            'title': <language neutral attribution>,
            'href': <url>
        },
        'download_links': [
            ['pdf', 'PDF', <url>],
            ['kml', 'KML', <url>],
            [<format>, <name>, <url>]
            ...
        ],
        'metadata_links': [
           ['text/xml', 'TC211', <url>],
           [<mime>, <name>, <url>],
           ...
        ]
      },
      ...
    ]}
    """
    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    # grab params directly to implement defaults as
    # opposed to panicy django forms behavior.
    query = params.get('q', '')
    try:
        start = int(params.get('start', '0'))
    except Exception:
        start = 0
    try:
        limit = min(int(params.get('limit', DEFAULT_SEARCH_BATCH_SIZE)),
                    MAX_SEARCH_BATCH_SIZE)
    except Exception:
        limit = DEFAULT_SEARCH_BATCH_SIZE


    sortby = params.get('sort','')
    sortorder= params.get('dir','')

    advanced = {}
    bbox = params.get('bbox', None)
    if bbox:
        try:
            bbox = [float(x) for x in bbox.split(',')]
            if len(bbox) == 4:
                advanced['bbox'] =  bbox
        except Exception:
            # ignore...
            pass

    result = _metadata_search(query, start, limit, sortby, sortorder, **advanced)

    # slowdown here to dig out result permissions and other info from GeoNode
    for doc in result['rows']:
        try:
            layer = Layer.objects.get(uuid=doc['uuid'])
            doc['_local'] = True
            doc['_permissions'] = {
                'view': request.user.has_perm('maps.view_layer', obj=layer),
                'change': request.user.has_perm('maps.change_layer', obj=layer),
                'delete': request.user.has_perm('maps.delete_layer', obj=layer),
                'change_permissions': request.user.has_perm('maps.change_layer_permissions', obj=layer),
            }
            if layer.topic_category:
                doc['topic_category'] = layer.topic_category.title
            if layer.owner:
                doc['owner_username'] = layer.owner.username
            if layer.temporal_extent_start:
                doc['temporal_extent_start'] = layer.temporal_extent_start
            if layer.temporal_extent_end:
                doc['temporal_extent_end'] = layer.temporal_extent_end

        except Layer.DoesNotExist:
            doc['_local'] = False
            pass

    result['success'] = True
    return HttpResponse(json.dumps(result), mimetype="application/json")

def _metadata_search(query, start, limit, sortby, sortorder, **kw):

    csw = get_csw()

    keywords = _split_query(query)

    if sortby:
        sortby = 'dc:' + sortby

    #Filter by category if present
    category = kw.get('topic_category', None)
    profile = kw.get('profile', None)

    cql = None
    if category or profile:
        cql = ""
        if category:
            cql += "topicCat = \'%s\'" % category
        if profile:
            cql += " and " if category else ""
            cql += "csw:AnyText like '%%profiles/%s/'" % profile

        for keyword in keywords:
            cql += " and csw:AnyText like '%%%s%%'" % keyword


    csw.getrecords(keywords=keywords, startposition=start+1, maxrecords=limit, bbox=kw.get('bbox', None), sortby=sortby, sortorder=sortorder, cql=cql)

    # build results
    # XXX this goes directly to the result xml doc to obtain
    # correct ordering and a fuller view of the result record
    # than owslib currently parses.  This could be improved by
    # improving owslib.
    results = [_build_search_result(doc) for doc in
               csw._exml.findall('//'+nspath('Record', namespaces['csw']))]

    result = {'rows': results,
              'total': csw.results['matches']}

    result['query_info'] = {
        'start': start,
        'limit': limit,
        'q': query
    }
    if start > 0:
        prev = max(start - limit, 0)
        params = urlencode({'q': query, 'start': prev, 'limit': limit})
        result['prev'] = reverse('geonode.maps.views.metadata_search') + '?' + params

    next_page = csw.results.get('nextrecord', 0)
    if next_page > 0:
        params = urlencode({'q': query, 'start': next_page - 1, 'limit': limit})
        result['next'] = reverse('geonode.maps.views.metadata_search') + '?' + params

    return result

def search_result_detail(request):
    uuid = request.GET.get("uuid", None)
    if  uuid is None:
        return HttpResponse(status=400)
    csw = get_csw()
    csw.getrecordbyid([uuid], outputschema=namespaces['gmd'])
    recs = csw.records.values()
    if len(recs) == 0:
        return HttpResponse(status=404)
    rec = recs[0]
    raw_xml = csw._exml.find(nspath('MD_Metadata', namespaces['gmd']))
    extra_links = _extract_links(rec, raw_xml)
    category = ''

    try:
        layer = Layer.objects.get(uuid=uuid)
        layer_is_remote = False
        category = layer.topic_category
    except Exception:
        layer = None
        layer_is_remote = True

    return render_to_response('maps/search_result_snippet.html', RequestContext(request, {
        'rec': rec,
        'extra_links': extra_links,
        'layer': layer,
        'layer_is_remote': layer_is_remote,
        'category' : category
    }))

def maps_search_result_detail(request):
    mapid = request.GET.get("mapid", None)
    if  mapid is None:
        return HttpResponse(status=400)
    try:
        map = Map.objects.get(id=mapid)
    except Exception:
        map = None

    return render_to_response('maps/search_result_snippet_map.html', RequestContext(request, {
        'map': map,
    }))

def _extract_links(rec, xml):
    download_links = []
    dl_type_path = "/".join([
        nspath("CI_OnlineResource", namespaces["gmd"]),
        nspath("protocol", namespaces["gmd"]),
        nspath("CharacterString", namespaces["gco"])
        ])

    dl_name_path = "/".join([
        nspath("CI_OnlineResource", namespaces["gmd"]),
        nspath("name", namespaces["gmd"]),
        nspath("CharacterString", namespaces["gco"])
        ])

    dl_description_path = "/".join([
        nspath("CI_OnlineResource", namespaces["gmd"]),
        nspath("description", namespaces["gmd"]),
        nspath("CharacterString", namespaces["gco"])
        ])

    dl_link_path = "/".join([
        nspath("CI_OnlineResource", namespaces["gmd"]),
        nspath("linkage", namespaces["gmd"]),
        nspath("URL", namespaces["gmd"])
        ])

    format_re = re.compile(".*\((.*)(\s*Format*\s*)\).*?")

    for link in xml.findall("*//" + nspath("onLine", namespaces['gmd'])):
        dl_type = link.find(dl_type_path)
        if dl_type is not None and dl_type.text == "WWW:DOWNLOAD-1.0-http--download":
            extension = link.find(dl_name_path).text.split('.')[-1]
            data_format = format_re.match(link.find(dl_description_path).text).groups()[0]
            url = link.find(dl_link_path).text
            download_links.append((extension, data_format, url))
    return dict(download=download_links)


def _build_search_result(doc):
    """
    accepts a node representing a csw result
    record and builds a POD structure representing
    the search result.
    """
    if doc is None:
        return None
    # Let owslib do some parsing for us...
    rec = CswRecord(doc)
    result = {}
    result['title'] = rec.title
    result['uuid'] = rec.identifier
    result['abstract'] = rec.abstract
    result['keywords'] = [x for x in rec.subjects if x]
    result['detail'] = rec.uri or ''

    # XXX needs indexing ? how
    result['attribution'] = {'title': '', 'href': ''}

    # XXX !_! pull out geonode 'typename' if there is one
    # index this directly...
    if rec.uri:
        try:
            result['name'] = urlparse(rec.uri).path.split('/')[-1]
        except Exception:
            pass
    # fallback: use geonetwork uuid
    if not result.get('name', ''):
        result['name'] = rec.identifier

    # Take BBOX from GeoNetwork Result...
    # XXX this assumes all our bboxes are in this
    # improperly specified SRS.
    if rec.bbox is not None and rec.bbox.crs == 'urn:ogc:def:crs:::WGS 1984':
        # slight workaround for ticket 530
        result['bbox'] = {
            'minx': min(rec.bbox.minx, rec.bbox.maxx),
            'maxx': max(rec.bbox.minx, rec.bbox.maxx),
            'miny': min(rec.bbox.miny, rec.bbox.maxy),
            'maxy': max(rec.bbox.miny, rec.bbox.maxy)
        }

    # XXX these could be exposed in owslib record...
    # locate all download links
    format_re = re.compile(".*\((.*)(\s*Format*\s*)\).*?")
    result['download_links'] = []
    for link_el in doc.findall(nspath('URI', namespaces['dc'])):
        if link_el.get('protocol', '') == 'WWW:DOWNLOAD-1.0-http--download':
            try:
                extension = link_el.get('name', '').split('.')[-1]
                data_format = format_re.match(link_el.get('description')).groups()[0]
                href = link_el.text
                result['download_links'].append((extension, data_format, href))
            except Exception:
                pass

    # construct the link to the geonetwork metadata record (not self-indexed)
    md_link = settings.GEONETWORK_BASE_URL + "srv/en/csw?" + urlencode({
            "request": "GetRecordById",
            "service": "CSW",
            "version": "2.0.2",
            "OutputSchema": "http://www.isotc211.org/2005/gmd",
            "ElementSetName": "full",
            "id": rec.identifier
        })
    result['metadata_links'] = [("text/xml", "TC211", md_link)]

    return result

def browse_data(request):
    return render_to_response('data.html', RequestContext(request, {}))

def search_page(request):
    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config()
    # for non-ajax requests, render a generic search page

    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    params = dict((escape(x),escape(y)) for x,y in params.iteritems())
    map_obj = Map(projection="EPSG:900913", zoom = 1, center_x = 0, center_y = 0)

    return render_to_response('search.html', RequestContext(request, {
        'init_search': json.dumps(params or {}),
        'viewer_config': json.dumps(map_obj.viewer_json(request.user, *DEFAULT_BASE_LAYERS)),
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
        "site" : settings.SITEURL
    }))

def change_poc(request, ids, template = 'maps/change_poc.html'):
    layers = Layer.objects.filter(id__in=ids.split('_'))
    if request.method == 'POST':
        form = PocForm(request.POST)
        if form.is_valid():
            for layer in layers:
                layer.poc = form.cleaned_data['contact']
                layer.save()
            # Process the data in form.cleaned_data
            # ...
            return HttpResponseRedirect('/admin/maps/layer') # Redirect after POST
    else:
        form = PocForm() # An unbound form
    return render_to_response(template, RequestContext(request,
                                  {'layers': layers, 'form': form }))


#### MAPS SEARCHING ####

DEFAULT_MAPS_SEARCH_BATCH_SIZE = 10
MAX_MAPS_SEARCH_BATCH_SIZE = 25
def maps_search(request):
    """
    handles a basic search for maps using the
    GeoNetwork catalog.

    the search accepts:
    q - general query for keywords across all fields
    start - skip to this point in the results
    limit - max records to return
    sort - field to sort results on
    dir - ASC or DESC, for ascending or descending order

    for ajax requests, the search returns a json structure
    like this:

    {
    'total': <total result count>,
    'next': <url for next batch if exists>,
    'prev': <url for previous batch if exists>,
    'query_info': {
        'start': <integer indicating where this batch starts>,
        'limit': <integer indicating the batch size used>,
        'q': <keywords used to query>,
    },
    'rows': [
      {
        'title': <map title,
        'abstract': '...',
        'detail' : <url geonode detail page>,
        'owner': <name of the map's owner>,
        'owner_detail': <url of owner's profile page>,
        'last_modified': <date and time of last modification>
      },
      ...
    ]}
    """
    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    params = dict((escape(x),escape(y)) for x,y in params.iteritems())

    # grab params directly to implement defaults as
    # opposed to panicy django forms behavior.
    query = params.get('q', '')
    try:
        start = int(params.get('start', '0'))
    except Exception:
        start = 0

    try:
        limit = min(int(params.get('limit', DEFAULT_MAPS_SEARCH_BATCH_SIZE)),
                    MAX_MAPS_SEARCH_BATCH_SIZE)
    except Exception:
        limit = DEFAULT_MAPS_SEARCH_BATCH_SIZE


    sort_field = params.get('sort', u'')
    sort_field = unicodedata.normalize('NFKD', sort_field).encode('ascii','ignore')
    sort_dir = params.get('dir', 'ASC')
    result = _maps_search(query, start, limit, sort_field, sort_dir)

    result['success'] = True
    return HttpResponse(json.dumps(result), mimetype="application/json")

def _maps_search(query, start, limit, sort_field, sort_dir):

    keywords = _split_query(query)
    map_query = Map.objects.filter()
    for keyword in keywords:
        map_query = map_query.filter(
              Q(title__icontains=keyword)
            | Q(keywords__name__icontains=keyword)
            | Q(abstract__icontains=keyword)).distinct()

    officialMaps = map_query.filter(~Q(officialurl=''))
    map_query = map_query.filter(Q(officialurl='') | Q(officialurl__isnull=True))

    if sort_field:
        order_by = ("" if sort_dir == "ASC" else "-") + sort_field
        map_query = map_query.order_by(order_by)
        officialMaps = officialMaps.order_by(order_by)

    maps_list = []
    allmaps = [i for i in itertools.chain(officialMaps,map_query)]

    for m in allmaps[start:start+limit]:
        try:
            owner_name = Contact.objects.get(user=m.owner).name
            if not owner_name:
                owner_name = m.owner.username
        except:
            if m.owner.first_name:
                owner_name = m.owner.first_name + " " + m.owner.last_name
            else:
                owner_name = m.owner.username

        url = ("/" + m.officialurl) if m.officialurl else ("/maps/" + m.urlsuffix) if m.urlsuffix  else "/maps/" + str(m.id)

        mapdict = {
            'id' : m.id,
            'title' : m.title,
            'abstract' : m.abstract,
            'urlsuffix' : m.urlsuffix,
            'detail' : url,
            'owner' : owner_name,
            'owner_detail' : reverse('profiles.views.profile_detail', args=(m.owner.username,)),
            'last_modified' : m.last_modified.isoformat()
            }
        maps_list.append(mapdict)

    result = {'rows': maps_list,
              'total': map_query.count()}

    result['query_info'] = {
        'start': start,
        'limit': limit,
        'q': query
    }
    if start > 0:
        prev = max(start - limit, 0)
        params = urlencode({'q': query, 'start': prev, 'limit': limit})
        result['prev'] = reverse('geonode.maps.views.maps_search') + '?' + params

    next_page = start + limit + 1
    if next_page < map_query.count():
        params = urlencode({'q': query, 'start': next_page - 1, 'limit': limit})
        result['next'] = reverse('geonode.maps.views.maps_search') + '?' + params

    return result

def maps_search_page(request):
    # for non-ajax requests, render a generic search page

    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    params = dict((escape(x),escape(y)) for x,y in params.iteritems())

    return render_to_response('maps_search.html', RequestContext(request, {
        'init_search': json.dumps(params or {}),
         "site" : settings.SITEURL
    }))

def batch_permissions_by_email(request):
    return batch_permissions(request, True)

def batch_permissions(request, use_email=False):
    if not request.user.is_authenticated:
        result = {'success': False, 'errors': ['You must log in to change permissions']}
        return HttpResponse(json.dumps(result), mimetype="application/json", status=401)

    if request.method != "POST":
        return HttpResponse("Permissions API requires POST requests", status=405)

    spec = json.loads(request.raw_post_data)

    if "layers" in spec:
        lyrs = Layer.objects.filter(pk__in = spec['layers'])
        for lyr in lyrs:
            if not request.user.has_perm("maps.change_layer_permissions", obj=lyr):
                return HttpResponse("User not authorized to change layer permissions", status=403)

    if "maps" in spec:
        maps = Map.objects.filter(pk__in = spec['maps'])
        for map in maps:
            if not request.user.has_perm("maps.change_map_permissions", obj=map):
                return HttpResponse("User not authorized to change map permissions", status=403)

    anon_level = spec['permissions'].get("anonymous")
    auth_level = spec['permissions'].get("authenticated")
    custom_level = spec['permissions'].get("customgroup")

    logger.debug("anon_level:[%s]; auth_level:[%s]; custom_level:[%s]", anon_level, auth_level, custom_level)

    users = spec['permissions'].get('users', [])
    user_names = [x for (x, y) in users]

    if "layers" in spec:
        lyrs = Layer.objects.filter(pk__in = spec['layers'])
        valid_perms = ['layer_readwrite', 'layer_readonly', 'layer_admin']
        if anon_level not in valid_perms:
            anon_level = "_none"
        if auth_level not in valid_perms:
            auth_level = "_none"
        if custom_level not in valid_perms:
            custom_level = "_none"

        logger.debug("anon:[%s],auth:[%s],custom:[%s]", anon_level, auth_level, custom_level)
        for lyr in lyrs:
            logger.info("Layer [%s]", lyr)
            if use_email:
                lyr.get_user_levels().exclude(user__email__in = user_names + [lyr.owner.email]).delete()
            else:
                lyr.get_user_levels().exclude(user__username__in = user_names + [lyr.owner.username]).delete()

            lyr.set_gen_level(ANONYMOUS_USERS, anon_level)
            lyr.set_gen_level(AUTHENTICATED_USERS, auth_level)
            lyr.set_gen_level(CUSTOM_GROUP_USERS, custom_level)
            for user, user_level in users:
                logger.info("User [%s]", user)

                if use_email:
                    user_obj = None
                    try:
                        user_obj = User.objects.get(email=user)
                    except User.DoesNotExist:
                        try:
                            user_obj = _create_new_user(user, lyr.title, reverse('geonode.maps.views.layer_detail', args=(lyr.typename,)), lyr.owner_id)
                        except:
                            logger.info("Could not create new user with email of %s" % user)
                    if user_level not in valid_perms:
                        user_level = "_none"
                    if user_obj:
                        lyr.set_user_level(user_obj, user_level)
                else:
                    if user_level not in valid_perms:
                        user_level = "_none"
                        user = User.objects.get(username=user)
                    lyr.set_user_level(user, user_level)


    if "maps" in spec:
        maps = Map.objects.filter(pk__in = spec['maps'])
        valid_perms = ['layer_readwrite', 'layer_readonly', 'layer_admin']
        if anon_level not in valid_perms:
            anon_level = "_none"
        if auth_level not in valid_perms:
            auth_level = "_none"
        if custom_level not in valid_perms:
            custom_level = "_none"
        anon_level = anon_level.replace("layer", "map")
        auth_level = auth_level.replace("layer", "map")
        custom_level = custom_level.replace("layer", "map")

        for m in maps:
            if use_email:
                m.get_user_levels().exclude(user__email__in = user_names + [m.owner.email]).delete()
            else:
                m.get_user_levels().exclude(user__username__in = user_names + [m.owner.username]).delete()
            m.set_gen_level(ANONYMOUS_USERS, anon_level)
            m.set_gen_level(AUTHENTICATED_USERS, auth_level)
            m.set_gen_level(CUSTOM_GROUP_USERS, custom_level)
            for user, user_level in spec['permissions'].get("users", []):
                user_level = user_level.replace("layer", "map")
                if user_level not in valid_perms:
                    user_level = "_none"

                if use_email:
                    m.get_user_levels().exclude(user__email__in = user_names + [m.owner.email]).delete()
                else:
                    m.get_user_levels().exclude(user__username__in = user_names + [m.owner.username]).delete()
                m.set_gen_level(ANONYMOUS_USERS, anon_level)
                m.set_gen_level(AUTHENTICATED_USERS, auth_level)
                m.set_gen_level(CUSTOM_GROUP_USERS, custom_level)
                for user, user_level in spec['permissions'].get("users", []):
                    user_level = user_level.replace("layer", "map")
                    if user_level not in valid_perms:
                        user_level = "_none"
                    if use_email:
                        user_obj = None
                        try:
                            user_obj = User.objects.get(email=user)
                        except User.DoesNotExist:
                            try:
                                user_obj = _create_new_user(user, m.title, reverse('geonode.maps.views.view', args=[m.id]), m.owner_id)
                            except:
                                logger.info("Could not create new user with email of %s" % user)
                        if user_obj:
                            m.set_user_level(userObject, user_level)
                    else:
                        m.set_user_level(user, user_level)

    return HttpResponse("Map/layer permissions updated")

def batch_delete(request):
    if not request.user.is_authenticated:
        return HttpResponse("You must log in to delete layers", status=401)

    if request.method != "POST":
        return HttpResponse("Delete API requires POST requests", status=405)

    spec = json.loads(request.raw_post_data)

    if "layers" in spec:
        lyrs = Layer.objects.filter(pk__in = spec['layers'])
        for lyr in lyrs:
            if not request.user.has_perm("maps.delete_layer", obj=lyr):
                return HttpResponse("User not authorized to delete layer", status=403)

    if "maps" in spec:
        map_query = Map.objects.filter(pk__in = spec['maps'])
        for m in map_query:
            if not request.user.has_perm("maps.delete_map", obj=m):
                return HttpResponse("User not authorized to delete map", status=403)

    if "layers" in spec:
        Layer.objects.filter(pk__in = spec["layers"]).delete()

    if "maps" in spec:
        Map.objects.filter(pk__in = spec["maps"]).delete()

    nlayers = len(spec.get('layers', []))
    nmaps = len(spec.get('maps', []))

    return HttpResponse("Deleted %d layers and %d maps" % (nlayers, nmaps))


class LayerCategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return '<a href="#" onmouseover=\'javascript:showModal("' + escape(obj.description) + '")\' onmouseout=\'javascript:hideModal()\';return false;\'>' + obj.title + '</a>'



class LayerCategoryForm(forms.Form):
    category_choice_field = LayerCategoryChoiceField(required=False, label = '*' + _('Category'), empty_label=None,
        queryset = LayerCategory.objects.extra(order_by = ['title']))


    def clean(self):
        cleaned_data = self.data
        ccf_data = cleaned_data.get("category_choice_field")


        if not ccf_data:
            msg = u"This field is required."
            self._errors = self.error_class([msg])




        # Always return the full collection of cleaned data.
        return cleaned_data



class LayerAttributeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(LayerAttributeForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.attribute_type != 'xsd:string':
            self.fields['searchable'].widget.attrs['disabled'] = True
        self.fields['attribute'].widget.attrs['readonly'] = True
        self.fields['display_order'].widget.attrs['size'] = 3



    class Meta:
        model = LayerAttribute
        exclude = ('attribute_type',)

def view_map_permissions(request, mapid):
    map = get_object_or_404(Map,pk=mapid)

    if not request.user.has_perm('maps.change_map_permissions', obj=map):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(request, {'error_message':
                                         _("You are not permitted to view this map's permissions")})), status=401)

    ctx = _view_perms_context(map, MAP_LEV_NAMES)
    ctx['map'] = map
    return render_to_response("maps/permissions.html", RequestContext(request, ctx))


def view_layer_permissions(request, layername):
    layer = get_object_or_404(Layer,typename=layername)

    if not request.user.has_perm('maps.change_layer_permissions', obj=layer):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(request, {'error_message':
                                         _("You are not permitted to view this layer's permissions")})), status=401)

    ctx = _view_perms_context(layer, LAYER_LEV_NAMES)
    ctx['layer'] = layer
    return render_to_response("maps/layer_permissions.html", RequestContext(request, ctx))



def ajax_layer_permissions_by_email(request, layername):
    return ajax_layer_permissions(request, layername, True)


def _perms_info_email(obj, level_names):
    info = obj.get_all_level_info_by_email()
    # these are always specified even if none
    info[ANONYMOUS_USERS] = info.get(ANONYMOUS_USERS, obj.LEVEL_NONE)
    info[AUTHENTICATED_USERS] = info.get(AUTHENTICATED_USERS, obj.LEVEL_NONE)
    info[CUSTOM_GROUP_USERS] = info.get(CUSTOM_GROUP_USERS, obj.LEVEL_NONE)
    info['users'] = sorted(info['users'].items())
    info['names'] = sorted(info['names'].items())
    info['levels'] = [(i, level_names[i]) for i in obj.permission_levels]
    if hasattr(obj, 'owner') and obj.owner is not None:
        info['owner'] = obj.owner.username
        info['owner_email'] = obj.owner.email
    return info

def _perms_info_email_json(obj, level_names):
    return json.dumps(_perms_info_email(obj, level_names))


def addlayers(request):
    # for non-ajax requests, render a generic search page

    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    map_obj = Map(projection="EPSG:900913", zoom = 1, center_x = 0, center_y = 0)

    return render_to_response('addlayers.html', RequestContext(request, {
        'init_search': json.dumps(params or {}),
        'viewer_config': json.dumps(map_obj.viewer_json(request.user, *DEFAULT_BASE_LAYERS)),
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
        "site" : settings.SITEURL
    }))

def addLayerJSON(request):
    logger.debug("Enter addLayerJSON")
    layername = request.GET.get('layername', False)
    logger.debug("layername is [%s]", layername)

    if layername:
        try:
            layer = Layer.objects.get(typename=layername)
            if not request.user.has_perm("maps.view_layer", obj=layer):
                return HttpResponse(status=401)
            sfJSON = {'layer': layer.layer_config(request.user)}
            logger.debug('sfJSON is [%s]', str(sfJSON))
            return HttpResponse(json.dumps(sfJSON))
        except Exception, e:
            logger.debug("Could not find matching layer: [%s]", str(e))
            return HttpResponse(str(e), status=500)

    else:
        return HttpResponse(status=500)


def ajax_layer_edit_check(request, layername):
    layer = get_object_or_404(Layer, typename=layername);
    editable = request.user.has_perm("maps.change_layer", obj=layer)
    return HttpResponse(
        str(editable),
        status=200 if editable else 403,
        mimetype='text/plain'
    )

def ajax_layer_update(request, layername):
    layer = get_object_or_404(Layer, typename=layername)
    if settings.USE_QUEUE:
        layer.queue_bounds_update()
        if settings.USE_GAZETTEER:
            layer.queue_gazetteer_update()
    else:
        layer.update_bounds()
        if settings.USE_GAZETTEER:
            layer.update_gazetteer()

    return HttpResponse(
        "Layer updated",
        status=200,
        mimetype='text/plain'
    )


def ajax_map_edit_check_permissions(request, mapid):
    mapeditlevel = 'None'
    if not request.user.has_perm("maps.change_map_permissions", obj=map):
        return HttpResponse(
            'You are not allowed to change permissions for this map',
            status=401,
            mimetype='text/plain'
        )

def ajax_map_permissions_by_email(request, mapid):
    return ajax_map_permissions(request, mapid, True)

def ajax_url_lookup(request):
    if request.method != 'POST':
        return HttpResponse(
            content='ajax user lookup requires HTTP POST',
            status=405,
            mimetype='text/plain'
        )
    elif 'query' not in request.POST:
        return HttpResponse(
            content='use a field named "query" to specify a prefix to filter urls',
            mimetype='text/plain'
        )
    if request.POST['query'] != '':
        forbiddenUrls = ['new','view',]
        maps = Map.objects.filter(urlsuffix__startswith=request.POST['query'])
        if request.POST['mapid'] != '':
            maps = maps.exclude(id=request.POST['mapid'])
        json_dict = {
            'urls': [({'url': m.urlsuffix}) for m in maps],
            'count': maps.count(),
            }
    else:
        json_dict = {
            'urls' : [],
            'count' : 0,
            }
    return HttpResponse(
        content=json.dumps(json_dict),
        mimetype='text/plain'
    )

def snapshot_config(snapshot, map, user):
    """
        Get the snapshot map configuration - look up WMS parameters (bunding box)
        for local GeoNode layers
    """
     #Match up the layer with it's source
    def snapsource_lookup(source, sources):
            for k, v in sources.iteritems():
                if v.get("id") == source.get("id"): return k
            return None

    #Set up the proper layer configuration
    def snaplayer_config(layer, sources, user):
        cfg = layer.layer_config(user)
        src_cfg = layer.source_config()
        source = snapsource_lookup(src_cfg, sources)
        if source: cfg["source"] = source
        if src_cfg.get("ptype", "gxp_wmscsource") == "gxp_wmscsource"  or src_cfg.get("ptype", "gxp_gnsource") == "gxp_gnsource" : cfg["buffer"] = 0
        return cfg


    decodedid = num_decode(snapshot)
    snapshot = get_object_or_404(MapSnapshot, pk=decodedid)
    if snapshot.map == map:
        config = json.loads(clean_config(snapshot.config))
        layers = [l for l in config["map"]["layers"]]
        sources = config["sources"]
        maplayers = []
        for ordering, layer in enumerate(layers):
            maplayers.append(
            map.layer_set.from_viewer_config(
                map, layer, config["sources"][layer["source"]], ordering))
        config['map']['layers'] = [snaplayer_config(l,sources,user) for l in maplayers]
    else:
        config = map.viewer_json(user)
    return config

def ajax_increment_layer_stats(request):
    if request.method != 'POST':
        return HttpResponse(
            content='ajax user lookup requires HTTP POST',
            status=405,
            mimetype='text/plain'
        )
    if request.POST['layername'] != '':
        layer_match = Layer.objects.filter(typename=request.POST['layername'])[:1]
        for l in layer_match:
            layerStats,created = LayerStats.objects.get_or_create(layer=l)
            layerStats.visits += 1
            first_visit = True
            if request.session.get('visitlayer' + str(l.id), False):
                first_visit = False
            else:
                request.session['visitlayer' + str(l.id)] = True
            if first_visit or created:
                layerStats.uniques += 1
            layerStats.save()

    return HttpResponse(
                            status=200
    )

def _create_new_user(user_email, map_layer_title, map_layer_url, map_layer_owner_id):
    random_password = User.objects.make_random_password()
    user_name = re.sub(r'\W', r'', user_email.split('@')[0])
    user_length = len(user_name)
    if user_length > 30:
        user_name = user_name[0:29]
    while len(User.objects.filter(username=user_name)) > 0:
        user_name = user_name[0:user_length-4] + User.objects.make_random_password(length=4, allowed_chars='0123456789')

    new_user = RegistrationProfile.objects.create_inactive_user(username=user_name, email=user_email, password=random_password, site = settings.SITE_ID, send_email=False)
    if new_user:
        #new_profile = Contact(user=new_user, name=new_user.username, email=new_user.email)
        new_profile = new_user.get_profile()
        if settings.USE_CUSTOM_ORG_AUTHORIZATION and new_user.email.endswith(settings.CUSTOM_GROUP_EMAIL_SUFFIX):
            new_profile.is_org_member = True
            new_profile.member_expiration_dt = datetime.today() + timedelta(days=365)
        new_profile.save()
        try:
            _send_permissions_email(user_email, map_layer_title, map_layer_url, map_layer_owner_id, random_password)
        except:
            logger.debug("An error ocurred when sending the mail")
    return new_user




def _send_permissions_email(user_email, map_layer_title, map_layer_url, map_layer_owner_id,  password):

    current_site = Site.objects.get_current()
    user = User.objects.get(email = user_email)
    profile = RegistrationProfile.objects.get(user=user)
    owner = User.objects.get(id=map_layer_owner_id)

    subject = render_to_string('registration/new_user_email_subject.txt',
            { 'site': current_site,
              'owner' : (owner.get_profile().name if owner.get_profile().name else owner.email),
              })
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    message = render_to_string('registration/new_user_email.txt',
            { 'activation_key': profile.activation_key,
              'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
              'owner': (owner.get_profile().name if owner.get_profile().name else owner.email),
              'title': map_layer_title,
              'url' : map_layer_url,
              'site': current_site,
              'username': user.username,
              'password' : password })

    send_mail(subject, message, settings.NO_REPLY_EMAIL, [user.email])

def get_suffix_if_custom(map):
    if map.use_custom_template:
        if map.officialurl:
            return map.officialurl
        elif map.urlsuffix:
            return map.urlsuffix
        else:
            return None
    else:
        return None

def official_site(request, site):
    """
    The view that returns the map composer opened to
    the map with the given official site url.
    """
    map_obj = get_object_or_404(Map,officialurl=site)
    return view(request, str(map_obj.id))

def official_site_mobile(request, site):
    """
    The view that returns the map composer opened to
    the map with the given official site url.
    """
    map_obj = get_object_or_404(Map,officialurl=site)
    return mobilemap(request, str(map_obj.id))


def official_site_controller(request, site):
    '''
    main view for map resources, dispatches to correct
    view based on method and query args.
    '''
    map_obj = get_object_or_404(Map,officialurl=site)
    return map_controller(request, str(map_obj.id))

def snapshot_create(request):
    """
    Create a permalinked map
    """
    conf = request.raw_post_data

    if isinstance(conf, basestring):
        config = json.loads(conf)
        snapshot = MapSnapshot.objects.create(config=clean_config(conf),map=Map.objects.get(id=config['id']))
        return HttpResponse(num_encode(snapshot.id), mimetype="text/plain")
    else:
        return HttpResponse("Invalid JSON", mimetype="text/plain", status=500)

def clean_config(conf):
    if isinstance(conf, basestring):
        config = json.loads(conf)
        config_extras = ["tools", "rest", "homeUrl", "localGeoServerBaseUrl", "localCSWBaseUrl", "csrfToken", "db_datastore", "authorizedRoles"]
        for config_item in config_extras:
            if config_item in config:
                del config[config_item ]
            if config_item in config["map"]:
                del config["map"][config_item ]
        return json.dumps(config)
    else:
        return conf

def ajax_snapshot_history(request, mapid):
    map_obj = Map.objects.get(pk=mapid)
    history = [snapshot.json() for snapshot in map_obj.snapshots]
    return HttpResponse(json.dumps(history), mimetype="text/plain")



@login_required
def deletemapnow(request, mapid):
    ''' Delete a map, and its constituent layers. '''
    map_obj = get_object_or_404(Map,pk=mapid)

    if not request.user.has_perm('maps.delete_map', obj=map):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(request, {'error_message':
                                         _("You are not permitted to delete this map.")})), status=401)

    layers = map_obj.layer_set.all()
    for layer in layers:
        layer.delete()

    snapshots = map_obj.snapshot_set.all()
    for snapshot in snapshots:
        snapshot.delete()
    map_obj.delete()

    return HttpResponseRedirect(request.user.get_profile().get_absolute_url())


def map_share(request,mapid):
    '''
    The view that shows map permissions in a window from map
    '''
    map = get_object_or_404(Map,pk=mapid)
    mapstats,created = MapStats.objects.get_or_create(map=map)


    if not request.user.has_perm('maps.view_map', obj=map):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(request, {'error_message':
                                         _("You are not allowed to view this map.")})), status=401)


    return render_to_response("maps/mapinfopanel.html", RequestContext(request, {
        "map": map,
        "mapstats": mapstats,
        'permissions_json': _perms_info_email_json(map, MAP_LEV_NAMES),
        'customGroup': settings.CUSTOM_GROUP_NAME if settings.USE_CUSTOM_ORG_AUTHORIZATION else '',
        }))

@login_required
def create_pg_layer(request):
    db_store_name = get_db_store_name(request.user)
    if request.method == 'GET':
        layer_form = LayerCreateForm(prefix="layer")

        # Determine if this page will be shown in a tabbed panel or full page
        pagetorender = "maps/layer_create_tab.html" if "tab" in request.GET else "maps/layer_create.html"


        return render_to_response(pagetorender, RequestContext(request, {
            "layer_form": layer_form,
            "customGroup": settings.CUSTOM_GROUP_NAME if settings.USE_CUSTOM_ORG_AUTHORIZATION else '',
            "geoms": GEOMETRY_CHOICES
        }))

    if request.method == 'POST':
        from geonode.maps.utils import check_projection, create_django_record, get_valid_layer_name
        from ordereddict import OrderedDict
        layer_form = LayerCreateForm(request.POST)
        if layer_form.is_valid():
            cat = Layer.objects.gs_catalog

            # Assume default workspace
            ws = cat.get_workspace(settings.DEFAULT_WORKSPACE)
            if ws is None:
                msg = 'Specified workspace [%s] not found' % settings.DEFAULT_WORKSPACE
                return HttpResponse(msg, status='400')

            # Assume datastore used for PostGIS
            store = db_store_name
            if store is None:
                msg = 'Specified store [%s] not found' % db_store_name
                return HttpResponse(msg, status='400')

            #TODO: Let users create their own schema
            attribute_list = [
                ["the_geom","com.vividsolutions.jts.geom." + layer_form.cleaned_data['geom'],{"nillable":False}],
                ["Name","java.lang.String",{"nillable":True}],
                ["Description","java.lang.String", {"nillable":True}],
                ["Start_Date","java.util.Date",{"nillable":True}],
                ["End_Date","java.util.Date",{"nillable":True}],
                ["String_Value_1","java.lang.String",{"nillable":True}],
                ["String_Value_2","java.lang.String", {"nillable":True}],
                ["Number_Value_1","java.lang.Float",{"nillable":True}],
                ["Number_Value_2","java.lang.Float", {"nillable":True}],
            ]

            # Add geometry to attributes dictionary, based on user input; use OrderedDict to remember order
            #attribute_list.insert(0,[u"the_geom",u"com.vividsolutions.jts.geom." + layer_form.cleaned_data['geom'],{"nillable":False}])

            name = get_valid_layer_name(layer_form.cleaned_data['name'])
            permissions = layer_form.cleaned_data["permissions"]

            try:
                logger.info("Create layer %s", name)
                layer = cat.create_native_layer(settings.DEFAULT_WORKSPACE,
                                          db_store_name,
                                          name,
                                          name,
                                          escape(layer_form.cleaned_data['title']),
                                          layer_form.cleaned_data['srs'],
                                          attribute_list)

                logger.info("Create default style")
                publishing = cat.get_layer(name)
                sld = get_sld_for(publishing)
                cat.create_style(name, sld)
                publishing.default_style = cat.get_style(name)
                cat.save(publishing)

                logger.info("Check projection")
                check_projection(name, layer)

                logger.info("Create django record")
                title = layer_form.cleaned_data['title']
                geonodeLayer = create_django_record(request.user, title, layer_form.cleaned_data['keywords'].strip().split(" "), layer_form.cleaned_data['abstract'], layer, permissions)

                # audit action
                username = request.user.get_profile().username()
                action = Action(
                    action_type='layer_create',
                    description='User %s created layer titled "%s"' % (username, title),
                    args=geonodeLayer.uuid,
                )
                action.save()

                redirect_to  = reverse('data_metadata', args=[geonodeLayer.typename])
                if 'mapid' in request.POST and request.POST['mapid'] == 'tab': #if mapid = tab then open metadata form in tabbed panel
                    redirect_to+= "?tab=worldmap_create_panel"
                elif 'mapid' in request.POST and request.POST['mapid'] != '': #if mapid = number then add to parameters and open in full page
                    redirect_to += "?map=" + request.POST['mapid']
                return HttpResponse(json.dumps({
                    "success": True,
                    "redirect_to": redirect_to}))
            except Exception, e:
                logger.exception("Unexpected error.")
                return HttpResponse(json.dumps({
                    "success": False,
                    "errors": ["Unexpected error: " + escape(str(e))]}))

        else:
            #The form has errors, what are they?
            return HttpResponse(layer_form.errors, status='500')

@login_required
def layer_contacts(request, layername):
    layer = get_object_or_404(Layer, typename=layername)
    if request.user.is_authenticated():
        if not request.user.has_perm('maps.change_layer', obj=layer):
            return HttpResponse(loader.render_to_string('401.html',
                RequestContext(request, {'error_message':
                                             _("You are not permitted to modify this layer's metadata")})), status=401)


    poc = layer.poc
    metadata_author = layer.metadata_author

    if request.method == "GET":
        contact_form = LayerContactForm(prefix="layer")
        if poc.user is None:
            poc_form = ContactProfileForm(instance=poc, prefix="poc")
        else:
            contact_form.fields['poc'].initial = poc.id
            poc_form = ContactProfileForm(prefix="poc")
            poc_form.hidden=True

        if metadata_author.user is None:
            author_form = ContactProfileForm(instance=metadata_author, prefix="author")
        else:
            contact_form.fields['metadata_author'].initial = metadata_author.id
            author_form = ContactProfileForm(prefix="author")
            author_form.hidden=True
    elif request.method == "POST":
        contact_form = LayerContactForm(request.POST, prefix="layer")
        if contact_form.is_valid():
            new_poc = contact_form.cleaned_data['poc']
            new_author = contact_form.cleaned_data['metadata_author']
            if new_poc is None:
                poc_form = ContactProfileForm(request.POST, prefix="poc")
                if poc_form.has_changed and poc_form.is_valid():
                    new_poc = poc_form.save()
            else:
                poc_form = ContactProfileForm(prefix="poc")
                poc_form.hidden=True

            if new_author is None:
                author_form = ContactProfileForm(request.POST, prefix="author")
                if author_form.has_changed and author_form.is_valid():
                    new_author = author_form.save()
            else:
                author_form = ContactProfileForm(prefix="author")
                author_form.hidden=True

            if new_poc is not None and new_author is not None:
                layer.poc = new_poc
                layer.metadata_author = new_author
                layer.save()
                return HttpResponseRedirect("/data/" + layer.typename)



    #Deal with a form submission via ajax
    if request.method == 'POST' and (not contact_form.is_valid()):
        data = render_to_response("maps/layer_contacts.html", RequestContext(request, {
            "layer": layer,
            "contact_form": contact_form,
            "poc_form": poc_form,
            "author_form": author_form,
            "lastmap" : request.session.get("lastmap"),
            "lastmapTitle" : request.session.get("lastmapTitle")
        }))
        return HttpResponse(data, status=412)

    #Display the view on a regular page
    return render_to_response("maps/layer_contacts.html", RequestContext(request, {
        "layer": layer,
        "contact_form": contact_form,
        "poc_form": poc_form,
        "author_form": author_form,
        "lastmap" : request.session.get("lastmap"),
        "lastmapTitle" : request.session.get("lastmapTitle")
    }))

def category_list():
    topics = LayerCategory.objects.all()
    topicArray = []
    for topic in topics:
        topicArray.append([topic.name, topic.title])
    return topicArray

def mobilemap(request, mapid=None, snapshot=None):
    if mapid is None:
        return newmap(request);
    else:
        if mapid.isdigit():
            map_obj = Map.objects.get(pk=mapid)
        else:
            map_obj = Map.objects.get(urlsuffix=mapid)

        if not request.user.has_perm('maps.view_map', obj=map_obj):
            return HttpResponse(_("Not Permitted"), status=401, mimetype="text/plain")
        if snapshot is None:
            config = map_obj.viewer_json(request.user)
        else:
            config = snapshot_config(snapshot, map_obj, request.user)

        first_visit_mobile = True
        if request.session.get('visit_mobile' + str(map_obj.id), False):
            first_visit_mobile = False
        else:
            request.session['visit_mobile' + str(map_obj.id)] = True
        config['first_visit_mobile'] = first_visit_mobile

    return render_to_response('maps/mobilemap.html', RequestContext(request, {
        'config': json.dumps(config),
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
        'GEONETWORK_BASE_URL' : settings.GEONETWORK_BASE_URL,
        'GEOSERVER_BASE_URL' : settings.GEOSERVER_BASE_URL,
        'DB_DATASTORE' : settings.DB_DATASTORE,
        'maptitle': map_obj.title,
        'urlsuffix': get_suffix_if_custom(map_obj),
    }))


@login_required
def users_remove(request):
    # delete multiple user from admin map page action
    users = []
    ids = ''
    if 'ids' in request.GET:
        ids = request.GET['ids']
    else:
        ids = request.POST['ids']
    maps = Map.objects.filter(id__in=ids.split(','))
    for map in maps:
        if map.owner not in users:
            users.append(map.owner)
    if request.method == 'GET':
        return render_to_response("maps/users_remove.html", RequestContext(request, {
            'users': users,
            'ids': ids,
        }))
    if request.method == 'POST':
        for user in users:
            print 'Removing user %s' % user.username
            user.delete()
        return HttpResponseRedirect(reverse('admin:maps_map_changelist'))

@login_required
def add_endpoint(request):
    """
    Let the user to add an endpoint for a remote service.
    """
    if request.method == 'POST':
        endpoint_form = EndpointForm(request.POST)
        if endpoint_form.is_valid():
            endpoint = endpoint_form.save(commit=False)
            endpoint.owner = request.user
            endpoint.save()
            return direct_to_template(
                request,
                'maps/endpoint_added.html', {
                    "endpoint": endpoint,
                }
            )
        else:
            logger.info('Error posting an endpoint')
    else:
        endpoint_form = EndpointForm()

    return render_to_response(
        'maps/endpoint_add.html',
        RequestContext(request, {
            "form": endpoint_form,
        })
    )
