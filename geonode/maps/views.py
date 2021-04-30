# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import math
import logging
import traceback
from urllib.parse import quote, urlsplit, urljoin
from itertools import chain

from guardian.shortcuts import get_perms

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.http import (
    HttpResponse, HttpResponseRedirect,
    HttpResponseNotAllowed, HttpResponseServerError, Http404)
from django.conf import settings
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods

import json
from django.db.models import F
from django.views.decorators.clickjacking import (
    xframe_options_exempt,
    xframe_options_sameorigin)
from geonode.decorators import check_keyword_write_perms
from geonode.layers.models import Layer
from geonode.maps.models import Map, MapLayer
from geonode.layers.views import _resolve_layer
from geonode.utils import (
    DEFAULT_TITLE,
    DEFAULT_ABSTRACT,
    build_social_links,
    http_client,
    forward_mercator,
    bbox_to_projection,
    default_map_config,
    resolve_object,
    check_ogc_backend)
from geonode.maps.forms import MapForm
from geonode.security.views import _perms_info_json
from geonode.base.forms import CategoryForm, TKeywordForm
from geonode.base.models import (
    Thesaurus,
    TopicCategory)
from geonode import geoserver
from geonode.groups.models import GroupProfile
from geonode.base.auth import get_or_create_token
from geonode.documents.models import get_related_documents
from geonode.people.forms import ProfileForm
from geonode.base.views import batch_modify
from .tasks import delete_map
from geonode.monitoring import register_event
from geonode.monitoring.models import EventType
from geonode.thumbs.thumbnails import create_thumbnail
from deprecated import deprecated

from dal import autocomplete

from geonode.base.utils import ManageResourceOwnerPermissions

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    # FIXME: The post service providing the map_status object
    # should be moved to geonode.geoserver.
    from geonode.geoserver.helpers import ogc_server_settings

logger = logging.getLogger("geonode.maps.views")

DEFAULT_MAPS_SEARCH_BATCH_SIZE = 10
MAX_MAPS_SEARCH_BATCH_SIZE = 25

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this map.")
_PERMISSION_MSG_GENERIC = _("You do not have permissions for this map.")
_PERMISSION_MSG_LOGIN = _("You must be logged in to save this map")
_PERMISSION_MSG_SAVE = _("You are not permitted to save or edit this map.")
_PERMISSION_MSG_METADATA = _(
    "You are not allowed to modify this map's metadata.")
_PERMISSION_MSG_VIEW = _("You are not allowed to view this map.")
_PERMISSION_MSG_UNKNOWN = _("An unknown error has occured.")


def _resolve_map(request, id, permission='base.change_resourcebase',
                 msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the Map by the provided typename and check the optional permission.
    '''
    if Map.objects.filter(urlsuffix=id).count() > 0:
        key = 'urlsuffix'
    else:
        key = 'pk'

    return resolve_object(request, Map, {key: id}, permission=permission,
                          permission_msg=msg, **kwargs)


# BASIC MAP VIEWS #
def map_detail(request, mapid, template='maps/map_detail.html'):
    '''
    The view that show details of each map
    '''
    try:
        map_obj = _resolve_map(
            request,
            mapid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not map_obj:
        raise Http404(_("Not found"))

    permission_manager = ManageResourceOwnerPermissions(map_obj)
    permission_manager.set_owner_permissions_according_to_workflow()

    # Add metadata_author or poc if missing
    map_obj.add_missing_metadata_author_or_poc()

    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    if request.user != map_obj.owner and not request.user.is_superuser:
        Map.objects.filter(
            id=map_obj.id).update(
            popular_count=F('popular_count') + 1)

    config = map_obj.viewer_json(request)

    register_event(request, EventType.EVENT_VIEW, map_obj.title)

    config = json.dumps(config)
    layers = MapLayer.objects.filter(map=map_obj.id)
    links = map_obj.link_set.download()

    # Call this first in order to be sure "perms_list" is correct
    permissions_json = _perms_info_json(map_obj)

    perms_list = get_perms(
        request.user,
        map_obj.get_self_resource()) + get_perms(request.user, map_obj)

    group = None
    if map_obj.group:
        try:
            group = GroupProfile.objects.get(slug=map_obj.group.name)
        except GroupProfile.DoesNotExist:
            group = None

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    context_dict = {
        'access_token': access_token,
        'config': config,
        'resource': map_obj,
        'group': group,
        'layers': layers,
        'perms_list': perms_list,
        'permissions_json': permissions_json,
        "documents": get_related_documents(map_obj),
        'links': links,
        'preview': getattr(
            settings,
            'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
            'mapstore'),
        'crs': getattr(
            settings,
            'DEFAULT_MAP_CRS',
            'EPSG:3857')
    }

    if settings.SOCIAL_ORIGINS:
        context_dict["social_links"] = build_social_links(request, map_obj)

    if request.user.is_authenticated:
        if getattr(settings, 'FAVORITE_ENABLED', False):
            from geonode.favorite.utils import get_favorite_info
            context_dict["favorite_info"] = get_favorite_info(request.user, map_obj)

    register_event(request, EventType.EVENT_VIEW, request.path)

    return render(request, template, context=context_dict)


@login_required
@check_keyword_write_perms
def map_metadata(
        request,
        mapid,
        template='maps/map_metadata.html',
        ajax=True):
    try:
        map_obj = _resolve_map(
            request,
            mapid,
            'base.change_resourcebase_metadata',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not map_obj:
        raise Http404(_("Not found"))

    # Add metadata_author or poc if missing
    map_obj.add_missing_metadata_author_or_poc()
    current_keywords = [keyword.name for keyword in map_obj.keywords.all()]
    poc = map_obj.poc

    metadata_author = map_obj.metadata_author

    topic_category = map_obj.category

    if request.method == "POST":
        map_form = MapForm(request.POST, instance=map_obj, prefix="resource")
        category_form = CategoryForm(request.POST, prefix="category_choice_field", initial=int(
            request.POST["category_choice_field"]) if "category_choice_field" in request.POST and
            request.POST["category_choice_field"] else None)
        tkeywords_form = TKeywordForm(request.POST)
    else:
        map_form = MapForm(instance=map_obj, prefix="resource")
        map_form.disable_keywords_widget_for_non_superuser(request.user)
        category_form = CategoryForm(
            prefix="category_choice_field",
            initial=topic_category.id if topic_category else None)

        # Keywords from THESAURUS management
        map_tkeywords = map_obj.tkeywords.all()
        tkeywords_list = ''
        lang = 'en'  # TODO: use user's language
        if map_tkeywords and len(map_tkeywords) > 0:
            tkeywords_ids = map_tkeywords.values_list('id', flat=True)
            if hasattr(settings, 'THESAURUS') and settings.THESAURUS:
                el = settings.THESAURUS
                thesaurus_name = el['name']
                try:
                    t = Thesaurus.objects.get(identifier=thesaurus_name)
                    for tk in t.thesaurus.filter(pk__in=tkeywords_ids):
                        tkl = tk.keyword.filter(lang=lang)
                        if len(tkl) > 0:
                            tkl_ids = ",".join(
                                map(str, tkl.values_list('id', flat=True)))
                            tkeywords_list += f",{tkl_ids}" if len(
                                tkeywords_list) > 0 else tkl_ids
                except Exception:
                    tb = traceback.format_exc()
                    logger.error(tb)

        tkeywords_form = TKeywordForm(instance=map_obj)

    if request.method == "POST" and map_form.is_valid(
    ) and category_form.is_valid():
        new_poc = map_form.cleaned_data['poc']
        new_author = map_form.cleaned_data['metadata_author']
        new_keywords = current_keywords if request.keyword_readonly else map_form.cleaned_data['keywords']
        new_regions = map_form.cleaned_data['regions']
        new_title = map_form.cleaned_data['title']
        new_abstract = map_form.cleaned_data['abstract']

        new_category = None
        if category_form and 'category_choice_field' in category_form.cleaned_data and\
                category_form.cleaned_data['category_choice_field']:
            new_category = TopicCategory.objects.get(
                id=int(category_form.cleaned_data['category_choice_field']))

        if new_poc is None:
            if poc is None:
                poc_form = ProfileForm(
                    request.POST,
                    prefix="poc",
                    instance=poc)
            else:
                poc_form = ProfileForm(request.POST, prefix="poc")
            if poc_form.has_changed and poc_form.is_valid():
                new_poc = poc_form.save()

        if new_author is None:
            if metadata_author is None:
                author_form = ProfileForm(request.POST, prefix="author",
                                          instance=metadata_author)
            else:
                author_form = ProfileForm(request.POST, prefix="author")
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        if new_poc is not None and new_author is not None:
            map_obj.poc = new_poc
            map_obj.metadata_author = new_author
        map_obj.title = new_title
        map_obj.abstract = new_abstract
        map_obj.keywords.clear()
        map_obj.keywords.add(*new_keywords)
        map_obj.regions.clear()
        map_obj.regions.add(*new_regions)
        map_obj.category = new_category

        register_event(request, EventType.EVENT_CHANGE_METADATA, map_obj)
        if not ajax:
            return HttpResponseRedirect(
                reverse(
                    'map_detail',
                    args=(
                        map_obj.id,
                    )))

        message = map_obj.id

        try:
            # Keywords from THESAURUS management
            # Rewritten to work with updated autocomplete
            if not tkeywords_form.is_valid():
                return HttpResponse(json.dumps({'message': "Invalid thesaurus keywords"}, status_code=400))

            thesaurus_setting = getattr(settings, 'THESAURUS', None)
            if thesaurus_setting:
                tkeywords_data = tkeywords_form.cleaned_data['tkeywords']
                tkeywords_data = tkeywords_data.filter(
                    thesaurus__identifier=thesaurus_setting['name']
                )
                map_obj.tkeywords.set(tkeywords_data)
            elif Thesaurus.objects.all().exists():
                fields = tkeywords_form.cleaned_data
                map_obj.tkeywords.set(tkeywords_form.cleanx(fields))

        except Exception:
            tb = traceback.format_exc()
            logger.error(tb)

        map_obj.save(notify=True)

        return HttpResponse(json.dumps({'message': message}))

    # - POST Request Ends here -

    # Request.GET
    if poc is None:
        poc_form = ProfileForm(request.POST, prefix="poc")
    else:
        map_form.fields['poc'].initial = poc.id
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden = True

    if metadata_author is None:
        author_form = ProfileForm(request.POST, prefix="author")
    else:
        map_form.fields['metadata_author'].initial = metadata_author.id
        author_form = ProfileForm(prefix="author")
        author_form.hidden = True

    config = map_obj.viewer_json(request)
    layers = MapLayer.objects.filter(map=map_obj.id)

    metadata_author_groups = []
    if request.user.is_superuser or request.user.is_staff:
        metadata_author_groups = GroupProfile.objects.all()
    else:
        try:
            all_metadata_author_groups = chain(
                request.user.group_list_all(),
                GroupProfile.objects.exclude(access="private"))
        except Exception:
            all_metadata_author_groups = GroupProfile.objects.exclude(
                access="private")
        [metadata_author_groups.append(item) for item in all_metadata_author_groups
            if item not in metadata_author_groups]

    if settings.ADMIN_MODERATE_UPLOADS:
        if not request.user.is_superuser:
            can_change_metadata = request.user.has_perm(
                'change_resourcebase_metadata',
                map_obj.get_self_resource())
            try:
                is_manager = request.user.groupmember_set.all().filter(role='manager').exists()
            except Exception:
                is_manager = False
            if not is_manager or not can_change_metadata:
                if settings.RESOURCE_PUBLISHING:
                    map_form.fields['is_published'].widget.attrs.update(
                        {'disabled': 'true'})
                map_form.fields['is_approved'].widget.attrs.update(
                    {'disabled': 'true'})

    register_event(request, EventType.EVENT_VIEW_METADATA, map_obj)
    return render(request, template, context={
        "config": json.dumps(config),
        "resource": map_obj,
        "map": map_obj,
        "map_form": map_form,
        "poc_form": poc_form,
        "author_form": author_form,
        "category_form": category_form,
        "tkeywords_form": tkeywords_form,
        "layers": layers,
        "preview": getattr(settings, 'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY', 'mapstore'),
        "crs": getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:3857'),
        "metadata_author_groups": metadata_author_groups,
        "TOPICCATEGORY_MANDATORY": getattr(settings, 'TOPICCATEGORY_MANDATORY', False),
        "GROUP_MANDATORY_RESOURCES": getattr(settings, 'GROUP_MANDATORY_RESOURCES', False),
    })


@login_required
def map_metadata_advanced(request, mapid):
    return map_metadata(
        request,
        mapid,
        template='maps/map_metadata_advanced.html')


@login_required
def map_remove(request, mapid, template='maps/map_remove.html'):
    ''' Delete a map, and its constituent layers. '''
    try:
        map_obj = _resolve_map(
            request,
            mapid,
            'base.delete_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not map_obj:
        raise Http404(_("Not found"))

    if request.method == 'GET':
        return render(request, template, context={
            "map": map_obj
        })
    elif request.method == 'POST':
        if getattr(settings, 'SLACK_ENABLED', False):
            slack_message = None
            try:
                from geonode.contrib.slack.utils import build_slack_message_map
                slack_message = build_slack_message_map("map_delete", map_obj)
            except Exception:
                logger.error("Could not build slack message for delete map.")
            delete_map.apply_async((map_obj.id, ))
            try:
                from geonode.contrib.slack.utils import send_slack_messages
                send_slack_messages(slack_message)
            except Exception:
                logger.error("Could not send slack message for delete map.")
        else:
            delete_map.apply_async((map_obj.id, ))

        register_event(request, EventType.EVENT_REMOVE, map_obj)

        return HttpResponseRedirect(reverse("maps_browse"))


@xframe_options_exempt
def map_embed(
        request,
        mapid=None,
        template='maps/map_embed.html'):
    if mapid is None:
        config = default_map_config(request)[0]
    else:
        map_obj = _resolve_map(
            request,
            mapid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)

        config = map_obj.viewer_json(request)
        register_event(request, EventType.EVENT_VIEW, map_obj)
    return render(request, template, context={
        'config': json.dumps(config)
    })


# MAPS VIEWER #


@require_http_methods(["GET", ])
def add_layer(request):
    """
    The view that returns the map composer opened to
    a given map and adds a layer on top of it.
    """
    map_id = request.GET.get('map_id')
    layer_name = request.GET.get('layer_name')
    try:
        map_obj = _resolve_map(
            request,
            map_id,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not map_obj:
        raise Http404(_("Not found"))

    return map_view(request, str(map_obj.id), layer_name=layer_name)


@xframe_options_sameorigin
def map_view(request, mapid, layer_name=None,
             template='maps/map_view.html'):
    """
    The view that returns the map composer opened to
    the map with the given map ID.
    """
    try:
        map_obj = _resolve_map(
            request,
            mapid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not map_obj:
        raise Http404(_("Not found"))

    config = map_obj.viewer_json(request)
    if layer_name:
        config = add_layers_to_map_config(
            request, map_obj, (layer_name, ), False)

    register_event(request, EventType.EVENT_VIEW, request.path)
    return render(request, template, context={
        'config': json.dumps(config),
        'map': map_obj,
        'preview': getattr(
            settings,
            'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
            'mapstore')
    })


def map_view_js(request, mapid):
    try:
        map_obj = _resolve_map(
            request,
            mapid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not map_obj:
        raise Http404(_("Not found"))

    config = map_obj.viewer_json(request)
    return HttpResponse(
        json.dumps(config),
        content_type="application/javascript")


def map_json_handle_get(request, mapid):
    try:
        map_obj = _resolve_map(
            request,
            mapid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not map_obj:
        raise Http404(_("Not found"))

    return HttpResponse(
        json.dumps(
            map_obj.viewer_json(request)))


def map_json_handle_put(request, mapid):
    if not request.user.is_authenticated:
        return HttpResponse(
            _PERMISSION_MSG_LOGIN,
            status=401,
            content_type="text/plain"
        )

    map_obj = Map.objects.get(id=mapid)
    if not request.user.has_perm(
        'change_resourcebase',
            map_obj.get_self_resource()):
        return HttpResponse(
            _PERMISSION_MSG_SAVE,
            status=401,
            content_type="text/plain"
        )
    try:
        map_obj.update_from_viewer(request.body, context={'request': request, 'mapId': mapid, 'map': map_obj})
        register_event(request, EventType.EVENT_CHANGE, map_obj)
        return HttpResponse(
            json.dumps(
                map_obj.viewer_json(request)))
    except ValueError as e:
        return HttpResponse(
            f"The server could not understand the request.{str(e)}",
            content_type="text/plain",
            status=400
        )


def map_json(request, mapid):
    if request.method == 'GET':
        return map_json_handle_get(request, mapid)
    elif request.method == 'PUT':
        return map_json_handle_put(request, mapid)


@xframe_options_sameorigin
def map_edit(request, mapid, template='maps/map_edit.html'):
    """
    The view that returns the map composer opened to
    the map with the given map ID.
    """
    try:
        map_obj = _resolve_map(
            request,
            mapid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not map_obj:
        raise Http404(_("Not found"))

    config = map_obj.viewer_json(request)

    return render(request, template, context={
        'mapId': mapid,
        'config': json.dumps(config),
        'map': map_obj,
        'preview': getattr(
            settings,
            'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
            'mapstore')
    })


# NEW MAPS #


def clean_config(conf):
    if isinstance(conf, str):
        config = json.loads(conf)
        config_extras = [
            "tools",
            "rest",
            "homeUrl",
            "localGeoServerBaseUrl",
            "localCSWBaseUrl",
            "csrfToken",
            "db_datastore",
            "authorizedRoles"]
        for config_item in config_extras:
            if config_item in config:
                del config[config_item]
            if config_item in config["map"]:
                del config["map"][config_item]
        return json.dumps(config)
    else:
        return conf


def new_map(request, template='maps/map_new.html'):
    map_obj, config = new_map_config(request)
    context_dict = {
        'config': config,
        'map': map_obj
    }
    context_dict["preview"] = getattr(
        settings,
        'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
        'mapstore')
    if isinstance(config, HttpResponse):
        return config
    else:
        return render(
            request,
            template,
            context=context_dict)


def new_map_json(request):
    if request.method == 'GET':
        map_obj, config = new_map_config(request)
        if isinstance(config, HttpResponse):
            return config
        else:
            return HttpResponse(config)
    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponse(
                'You must be logged in to save new maps',
                content_type="text/plain",
                status=401
            )

        map_obj = Map(owner=request.user, zoom=0,
                      center_x=0, center_y=0)
        map_obj.save()
        map_obj.set_default_permissions()
        map_obj.handle_moderated_uploads()
        # If the body has been read already, use an empty string.
        # See https://github.com/django/django/commit/58d555caf527d6f1bdfeab14527484e4cca68648
        # for a better exception to catch when we move to Django 1.7.
        try:
            body = request.body
        except Exception:
            body = ''

        try:
            map_obj.update_from_viewer(body, context={'request': request, 'mapId': map_obj.id, 'map': map_obj})
        except ValueError as e:
            return HttpResponse(str(e), status=400)
        else:
            register_event(request, EventType.EVENT_UPLOAD, map_obj)
            return HttpResponse(
                json.dumps({'id': map_obj.id}),
                status=200,
                content_type='application/json'
            )
    else:
        return HttpResponse(status=405)


def new_map_config(request):
    '''
    View that creates a new map.

    If the query argument 'copy' is given, the initial map is
    a copy of the map with the id specified, otherwise the
    default map configuration is used.  If copy is specified
    and the map specified does not exist a 404 is returned.
    '''
    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config(request)

    map_obj = None
    if request.method == 'GET' and 'copy' in request.GET:
        mapid = request.GET['copy']
        try:
            map_obj = _resolve_map(
                request,
                mapid,
                'base.view_resourcebase')
        except PermissionDenied:
            return HttpResponse(_("Not allowed"), status=403)
        except Exception:
            raise Http404(_("Not found"))
        if not map_obj:
            raise Http404(_("Not found"))

        map_obj.abstract = DEFAULT_ABSTRACT
        map_obj.title = DEFAULT_TITLE
        if request.user.is_authenticated:
            map_obj.owner = request.user

        config = map_obj.viewer_json(request)
        del config['id']
    else:
        if request.method == 'GET':
            params = request.GET
        elif request.method == 'POST':
            params = request.POST
        else:
            return HttpResponse(status=405)

        if 'layer' in params:
            map_obj = Map(projection=getattr(settings, 'DEFAULT_MAP_CRS',
                                             'EPSG:3857'))
            config = add_layers_to_map_config(
                request, map_obj, params.getlist('layer'))
        else:
            config = DEFAULT_MAP_CONFIG
    if map_obj:
        map_obj.handle_moderated_uploads()
    return map_obj, json.dumps(config)


def add_layers_to_map_config(
        request, map_obj, layer_names, add_base_layers=True):
    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config(request)

    bbox = []
    layers = []
    for layer_name in layer_names:
        try:
            layer = _resolve_layer(request, layer_name)
        except ObjectDoesNotExist:
            # bad layer, skip
            continue
        except Http404:
            # can't find the layer, skip it.
            continue

        if not request.user.has_perm(
                'view_resourcebase',
                obj=layer.get_self_resource()):
            # invisible layer, skip inclusion
            continue

        layer_bbox = layer.bbox[0:4]
        bbox = layer_bbox[:]
        bbox[0] = layer_bbox[0]
        bbox[1] = layer_bbox[2]
        bbox[2] = layer_bbox[1]
        bbox[3] = layer_bbox[3]
        # assert False, str(layer_bbox)

        def decimal_encode(bbox):
            import decimal
            _bbox = []
            for o in [float(coord) for coord in bbox]:
                if isinstance(o, decimal.Decimal):
                    o = (str(o) for o in [o])
                _bbox.append(o)
            # Must be in the form : [x0, x1, y0, y1
            return [_bbox[0], _bbox[2], _bbox[1], _bbox[3]]

        def sld_definition(style):
            _sld = {
                "title": style.sld_title or style.name,
                "legend": {
                    "height": "40",
                    "width": "22",
                    "href": f"{layer.ows_url}?service=wms&request=GetLegendGraphic&format=image%2Fpng&width=20&height=20&layer={quote(layer.service_typename, safe='')}",
                    "format": "image/png"},
                "name": style.name}
            return _sld

        config = layer.attribute_config()
        if hasattr(layer, 'srid'):
            config['crs'] = {
                'type': 'name',
                'properties': layer.srid
            }
        # Add required parameters for GXP lazy-loading
        attribution = f"{layer.owner.first_name} {layer.owner.last_name}" if layer.owner.first_name or layer.owner.last_name else str(
            layer.owner)
        srs = getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:3857')
        srs_srid = int(srs.split(":")[1]) if srs != "EPSG:900913" else 3857
        config["attribution"] = f"<span class='gx-attribution-title'>{attribution}</span>"
        config["format"] = getattr(
            settings, 'DEFAULT_LAYER_FORMAT', 'image/png')
        config["title"] = layer.title
        config["wrapDateLine"] = True
        config["visibility"] = True
        config["srs"] = srs
        config["bbox"] = decimal_encode(
            bbox_to_projection([float(coord) for coord in layer_bbox] + [layer.srid, ],
                               target_srid=int(srs.split(":")[1]))[:4])
        config["capability"] = {
            "abstract": layer.abstract,
            "store": layer.store,
            "name": layer.alternate,
            "title": layer.title,
            "style": '',
            "queryable": True,
            "storeType": layer.storeType,
            "bbox": {
                layer.srid: {
                    "srs": layer.srid,
                    "bbox": decimal_encode(bbox)
                },
                srs: {
                    "srs": srs,
                    "bbox": decimal_encode(
                        bbox_to_projection([float(coord) for coord in layer_bbox] + [layer.srid, ],
                                           target_srid=srs_srid)[:4])
                },
                "EPSG:4326": {
                    "srs": "EPSG:4326",
                    "bbox": decimal_encode(bbox) if layer.srid == 'EPSG:4326' else
                    bbox_to_projection(
                        [float(coord) for coord in layer_bbox] + [layer.srid, ], target_srid=4326)[:4]
                },
                "EPSG:900913": {
                    "srs": "EPSG:900913",
                    "bbox": decimal_encode(bbox) if layer.srid == 'EPSG:900913' else
                    bbox_to_projection(
                        [float(coord) for coord in layer_bbox] + [layer.srid, ], target_srid=3857)[:4]
                }
            },
            "srs": {
                srs: True
            },
            "formats": ["image/png", "application/atom xml", "application/atom+xml", "application/json;type=utfgrid",
                        "application/openlayers", "application/pdf", "application/rss xml", "application/rss+xml",
                        "application/vnd.google-earth.kml", "application/vnd.google-earth.kml xml",
                        "application/vnd.google-earth.kml+xml", "application/vnd.google-earth.kml+xml;mode=networklink",
                        "application/vnd.google-earth.kmz", "application/vnd.google-earth.kmz xml",
                        "application/vnd.google-earth.kmz+xml", "application/vnd.google-earth.kmz;mode=networklink",
                        "atom", "image/geotiff", "image/geotiff8", "image/gif", "image/gif;subtype=animated",
                        "image/jpeg", "image/png8", "image/png; mode=8bit", "image/svg", "image/svg xml",
                        "image/svg+xml", "image/tiff", "image/tiff8", "image/vnd.jpeg-png",
                        "kml", "kmz", "openlayers", "rss", "text/html; subtype=openlayers", "utfgrid"],
            "attribution": {
                "title": attribution
            },
            "infoFormats": ["text/plain", "application/vnd.ogc.gml", "text/xml", "application/vnd.ogc.gml/3.1.1",
                            "text/xml; subtype=gml/3.1.1", "text/html", "application/json"],
            "styles": [sld_definition(s) for s in layer.styles.all()],
            "prefix": layer.alternate.split(":")[0] if ":" in layer.alternate else "",
            "keywords": [k.name for k in layer.keywords.all()] if layer.keywords else [],
            "llbbox": decimal_encode(bbox) if layer.srid == 'EPSG:4326' else
            bbox_to_projection(
                [float(coord) for coord in layer_bbox] + [layer.srid, ], target_srid=4326)[:4]
        }

        all_times = None
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            if layer.has_time:
                from geonode.geoserver.views import get_capabilities
                # WARNING Please make sure to have enabled DJANGO CACHE as per
                # https://docs.djangoproject.com/en/2.0/topics/cache/#filesystem-caching
                wms_capabilities_resp = get_capabilities(
                    request, layer.id, tolerant=True)
                if wms_capabilities_resp.status_code >= 200 and wms_capabilities_resp.status_code < 400:
                    wms_capabilities = wms_capabilities_resp.getvalue()
                    if wms_capabilities:
                        from defusedxml import lxml as dlxml
                        namespaces = {'wms': 'http://www.opengis.net/wms',
                                      'xlink': 'http://www.w3.org/1999/xlink',
                                      'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
                        e = dlxml.fromstring(wms_capabilities)
                        for atype in e.findall(
                                f"./[wms:Name='{layer.alternate}']/wms:Dimension[@name='time']", namespaces):
                            dim_name = atype.get('name')
                            if dim_name:
                                dim_name = str(dim_name).lower()
                                if dim_name == 'time':
                                    dim_values = atype.text
                                    if dim_values:
                                        all_times = dim_values.split(",")
                                        break
                if all_times:
                    config["capability"]["dimensions"] = {
                        "time": {
                            "name": "time",
                            "units": "ISO8601",
                            "unitsymbol": None,
                            "nearestVal": False,
                            "multipleVal": False,
                            "current": False,
                            "default": "current",
                            "values": all_times
                        }
                    }

        if layer.storeType == "remoteStore":
            service = layer.remote_service
            source_params = {}
            if service.type in ('REST_MAP', 'REST_IMG'):
                source_params = {
                    "ptype": service.ptype,
                    "remote": True,
                    "url": service.service_url,
                    "name": service.name,
                    "title": f"[R] {service.title}"}
            maplayer = MapLayer(map=map_obj,
                                name=layer.alternate,
                                ows_url=layer.ows_url,
                                layer_params=json.dumps(config),
                                visibility=True,
                                source_params=json.dumps(source_params)
                                )
        else:
            ogc_server_url = urlsplit(
                ogc_server_settings.PUBLIC_LOCATION).netloc
            layer_url = urlsplit(layer.ows_url).netloc

            access_token = request.session['access_token'] if request and 'access_token' in request.session else None
            if access_token and ogc_server_url == layer_url and 'access_token' not in layer.ows_url:
                url = f'{layer.ows_url}?access_token={access_token}'
            else:
                url = layer.ows_url
            maplayer = MapLayer(
                map=map_obj,
                name=layer.alternate,
                ows_url=url,
                # use DjangoJSONEncoder to handle Decimal values
                layer_params=json.dumps(config, cls=DjangoJSONEncoder),
                visibility=True
            )

        layers.append(maplayer)

    if bbox and len(bbox) >= 4:
        minx, maxx, miny, maxy = [float(coord) for coord in bbox]
        x = (minx + maxx) / 2
        y = (miny + maxy) / 2

        if getattr(
            settings,
            'DEFAULT_MAP_CRS',
                'EPSG:3857') == "EPSG:4326":
            center = list((x, y))
        else:
            center = list(forward_mercator((x, y)))

        if center[1] == float('-inf'):
            center[1] = 0

        BBOX_DIFFERENCE_THRESHOLD = 1e-5

        # Check if the bbox is invalid
        valid_x = (maxx - minx) ** 2 > BBOX_DIFFERENCE_THRESHOLD
        valid_y = (maxy - miny) ** 2 > BBOX_DIFFERENCE_THRESHOLD

        if valid_x:
            width_zoom = math.log(360 / abs(maxx - minx), 2)
        else:
            width_zoom = 15

        if valid_y:
            height_zoom = math.log(360 / abs(maxy - miny), 2)
        else:
            height_zoom = 15

        map_obj.center_x = center[0]
        map_obj.center_y = center[1]
        map_obj.zoom = math.ceil(min(width_zoom, height_zoom))

    map_obj.handle_moderated_uploads()

    if add_base_layers:
        layers_to_add = DEFAULT_BASE_LAYERS + layers
    else:
        layers_to_add = layers
    config = map_obj.viewer_json(
        request, *layers_to_add)

    config['fromLayer'] = True
    return config


# MAPS DOWNLOAD #

def map_download(request, mapid, template='maps/map_download.html'):
    """
    Download all the layers of a map as a batch
    XXX To do, remove layer status once progress id done
    This should be fix because
    """
    try:
        map_obj = _resolve_map(
            request,
            mapid,
            'base.download_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not map_obj:
        raise Http404(_("Not found"))

    map_status = dict()
    if request.method == 'POST':

        def perm_filter(layer):
            return request.user.has_perm(
                'base.view_resourcebase',
                obj=layer.get_self_resource())

        mapJson = map_obj.json(perm_filter)

        # we need to remove duplicate layers
        j_map = json.loads(mapJson)
        j_layers = j_map["layers"]
        for j_layer in j_layers:
            if j_layer["service"] is None:
                j_layers.remove(j_layer)
                continue
            if (len([_l for _l in j_layers if _l == j_layer])) > 1:
                j_layers.remove(j_layer)
        mapJson = json.dumps(j_map)

        # the path to geoserver backend continue here
        url = urljoin(settings.SITEURL,
                      reverse("download-map", kwargs={'mapid': mapid}))
        resp, content = http_client.request(url, 'POST', data=mapJson)

        status = int(resp.status_code)

        if status == 200:
            map_status = json.loads(content)
            request.session["map_status"] = map_status
        else:
            raise Exception(
                f'Could not start the download of {map_obj.title}. Error was: {content}')

    locked_layers = []
    remote_layers = []
    downloadable_layers = []

    for lyr in map_obj.layer_set.all():
        if lyr.group != "background":
            if not lyr.local:
                remote_layers.append(lyr)
            else:
                ownable_layer = Layer.objects.get(alternate=lyr.name)
                if not request.user.has_perm(
                        'download_resourcebase',
                        obj=ownable_layer.get_self_resource()):
                    locked_layers.append(lyr)
                else:
                    # we need to add the layer only once
                    if len(
                            [_l for _l in downloadable_layers if _l.name == lyr.name]) == 0:
                        downloadable_layers.append(lyr)
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL

    register_event(request, EventType.EVENT_DOWNLOAD, map_obj)

    return render(request, template, context={
        "geoserver": ogc_server_settings.PUBLIC_LOCATION,
        "map_status": map_status,
        "map": map_obj,
        "locked_layers": locked_layers,
        "remote_layers": remote_layers,
        "downloadable_layers": downloadable_layers,
        "site": site_url
    })


def map_wmc(request, mapid, template="maps/wmc.xml"):
    """Serialize an OGC Web Map Context Document (WMC) 1.1"""
    try:
        map_obj = _resolve_map(
            request,
            mapid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not map_obj:
        raise Http404(_("Not found"))

    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    return render(request, template, context={
        'map': map_obj,
        'siteurl': site_url,
    }, content_type='text/xml')


@deprecated(version='2.10.1', reason="APIs have been changed on geospatial service")
def map_wms(request, mapid):
    """
    Publish local map layers as group layer in local OWS.

    /maps/:id/wms

    GET: return endpoint information for group layer,
    PUT: update existing or create new group layer.
    """
    try:
        map_obj = _resolve_map(
            request,
            mapid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not map_obj:
        raise Http404(_("Not found"))

    if request.method == 'PUT':
        try:
            layerGroupName = map_obj.publish_layer_group()
            response = dict(
                layerGroupName=layerGroupName,
                ows=getattr(ogc_server_settings, 'ows', ''),
            )
            register_event(request, EventType.EVENT_PUBLISH, map_obj)
            return HttpResponse(
                json.dumps(response),
                content_type="application/json")
        except Exception:
            return HttpResponseServerError()

    if request.method == 'GET':
        response = dict(
            layerGroupName=getattr(map_obj.layer_group, 'name', ''),
            ows=getattr(ogc_server_settings, 'ows', ''),
        )
        return HttpResponse(
            json.dumps(response),
            content_type="application/json")

    return HttpResponseNotAllowed(['PUT', 'GET'])


def maplayer_attributes(request, layername):
    # Return custom layer attribute labels/order in JSON format
    layer = Layer.objects.get(alternate=layername)
    return HttpResponse(
        json.dumps(
            layer.attribute_config()),
        content_type="application/json")


def get_suffix_if_custom(map):
    if map.use_custom_template:
        if map.featuredurl:
            return map.featuredurl
        elif map.urlsuffix:
            return map.urlsuffix
        else:
            return None
    else:
        return None


def featured_map(request, site):
    """
    The view that returns the map composer opened to
    the map with the given official site url.
    """
    map_obj = resolve_object(request,
                             Map,
                             {'featuredurl': site},
                             permission='base.view_resourcebase',
                             permission_msg=_PERMISSION_MSG_VIEW)
    return map_view(request, str(map_obj.id))


def featured_map_info(request, site):
    '''
    main view for map resources, dispatches to correct
    view based on method and query args.
    '''
    map_obj = resolve_object(request,
                             Map,
                             {'featuredurl': site},
                             permission='base.view_resourcebase',
                             permission_msg=_PERMISSION_MSG_VIEW)
    return map_detail(request, str(map_obj.id))


def ajax_url_lookup(request):
    if request.method != 'POST':
        return HttpResponse(
            content='ajax user lookup requires HTTP POST',
            status=405,
            content_type='text/plain'
        )
    elif 'query' not in request.POST:
        return HttpResponse(
            content='use a field named "query" to specify a prefix to filter urls',
            content_type='text/plain')
    if request.POST['query'] != '':
        maps = Map.objects.filter(urlsuffix__startswith=request.POST['query'])
        if request.POST['mapid'] != '':
            maps = maps.exclude(id=request.POST['mapid'])
        json_dict = {
            'urls': [({'url': m.urlsuffix}) for m in maps],
            'count': maps.count(),
        }
    else:
        json_dict = {
            'urls': [],
            'count': 0,
        }
    return HttpResponse(
        content=json.dumps(json_dict),
        content_type='text/plain'
    )


@require_http_methods(["POST"])
def map_thumbnail(request, mapid):
    try:
        map_obj = _resolve_map(request, mapid)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not map_obj:
        raise Http404(_("Not found"))

    try:

        request_body = json.loads(request.body)
        bbox = request_body['bbox'] + [request_body['srid']]
        zoom = request_body.get('zoom', None)

        create_thumbnail(map_obj, bbox=bbox, background_zoom=zoom, overwrite=True)

        return HttpResponse('Thumbnail saved')

    except Exception as e:
        logger.exception(e)

        return HttpResponse(
            content=_('error saving thumbnail'),
            status=500,
            content_type='text/plain'
        )


def map_metadata_detail(
        request,
        mapid,
        template='maps/map_metadata_detail.html'):
    try:
        map_obj = _resolve_map(
            request,
            mapid,
            'view_resourcebase')
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not map_obj:
        raise Http404(_("Not found"))

    group = None
    if map_obj.group:
        try:
            group = GroupProfile.objects.get(slug=map_obj.group.name)
        except GroupProfile.DoesNotExist:
            group = None
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    register_event(request, EventType.EVENT_VIEW_METADATA, map_obj)
    return render(request, template, context={
        "resource": map_obj,
        "group": group,
        'SITEURL': site_url
    })


@login_required
def map_batch_metadata(request):
    return batch_modify(request, 'Map')


class MapAutocomplete(autocomplete.Select2QuerySetView):

    # Overriding both result label methods to ensure autocomplete labels display without ' by user' suffix
    def get_selected_result_label(self, result):
        """Return the label of a selected result."""
        return self.get_result_label(result)

    def get_result_label(self, result):
        """Return the label of a selected result."""
        return str(result.title)

    def get_queryset(self):
        qs = Map.objects.all()

        if self.q:
            qs = qs.filter(title__icontains=self.q).order_by('title')[:100]

        return qs
