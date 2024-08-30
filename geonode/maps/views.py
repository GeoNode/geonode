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
import json
import logging
import traceback
import warnings
from urllib.parse import urljoin

from deprecated import deprecated
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_exempt

from geonode import geoserver
from geonode.base import register_event
from geonode.base.auth import get_or_create_token
from geonode.base.forms import CategoryForm, ThesaurusAvailableForm, TKeywordForm
from geonode.base.models import ExtraMetadata, Thesaurus, TopicCategory
from geonode.base.views import batch_modify
from geonode.client.hooks import hookset
from geonode.resource.manager import resource_manager
from geonode.decorators import check_keyword_write_perms
from geonode.groups.models import GroupProfile
from geonode.layers.models import Dataset
from geonode.maps.contants import _PERMISSION_MSG_DELETE  # noqa: used by mapstore
from geonode.maps.contants import _PERMISSION_MSG_SAVE  # noqa: used by mapstore
from geonode.maps.contants import (
    _PERMISSION_MSG_GENERIC,
    _PERMISSION_MSG_VIEW,
    MSG_NOT_ALLOWED,
    MSG_NOT_FOUND,
)
from geonode.maps.forms import MapForm
from geonode.maps.models import Map, MapLayer
from geonode.monitoring.models import EventType
from geonode.people.forms import ProfileForm
from geonode.security.utils import get_user_visible_groups
from geonode.utils import check_ogc_backend, http_client, resolve_object

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    # FIXME: The post service providing the map_status object
    # should be moved to geonode.geoserver.
    from geonode.geoserver.helpers import ogc_server_settings

logger = logging.getLogger("geonode.maps.views")


def _resolve_map(request, id, permission="base.change_resourcebase", msg=_PERMISSION_MSG_GENERIC, **kwargs):
    """
    Resolve the Map by the provided typename and check the optional permission.
    """
    key = "urlsuffix" if Map.objects.filter(urlsuffix=id).exists() else "pk"

    map_obj = resolve_object(request, Map, {key: id}, permission=permission, permission_msg=msg, **kwargs)
    return map_obj


@login_required
@check_keyword_write_perms
def map_metadata(
    request,
    mapid,
    template="maps/map_metadata.html",
    ajax=True,
    panel_template="layouts/map_panels.html",
    custom_metadata=None,
):
    try:
        map_obj = _resolve_map(request, mapid, "base.change_resourcebase_metadata", _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(MSG_NOT_ALLOWED, status=403)
    except Exception:
        raise Http404(MSG_NOT_FOUND)
    if not map_obj:
        raise Http404(MSG_NOT_FOUND)

    # Add metadata_author or poc if missing
    map_obj.add_missing_metadata_author_or_poc()

    current_keywords = [keyword.name for keyword in map_obj.keywords.all()]
    topic_thesaurus = map_obj.tkeywords.all()

    topic_category = map_obj.category

    if request.method == "POST":
        map_form = MapForm(request.POST, instance=map_obj, prefix="resource", user=request.user)
        category_form = CategoryForm(
            request.POST,
            prefix="category_choice_field",
            initial=(
                int(request.POST["category_choice_field"])
                if "category_choice_field" in request.POST and request.POST["category_choice_field"]
                else None
            ),
        )

        if hasattr(settings, "THESAURUS"):
            tkeywords_form = TKeywordForm(request.POST)
        else:
            tkeywords_form = ThesaurusAvailableForm(request.POST, prefix="tkeywords")
    else:
        map_form = MapForm(instance=map_obj, prefix="resource", user=request.user)
        map_form.disable_keywords_widget_for_non_superuser(request.user)
        category_form = CategoryForm(
            prefix="category_choice_field", initial=topic_category.id if topic_category else None
        )

        # Keywords from THESAURUS management
        map_tkeywords = map_obj.tkeywords.all()
        tkeywords_list = ""
        # Create THESAURUS widgets
        lang = "en"
        if hasattr(settings, "THESAURUS") and settings.THESAURUS:
            warnings.warn(
                "The settings for Thesaurus has been moved to Model, \
            this feature will be removed in next releases",
                DeprecationWarning,
            )
            tkeywords_list = ""
            if map_tkeywords and len(map_tkeywords) > 0:
                tkeywords_ids = map_tkeywords.values_list("id", flat=True)
                if hasattr(settings, "THESAURUS") and settings.THESAURUS:
                    el = settings.THESAURUS
                    thesaurus_name = el["name"]
                    try:
                        t = Thesaurus.objects.get(identifier=thesaurus_name)
                        for tk in t.thesaurus.filter(pk__in=tkeywords_ids):
                            tkl = tk.keyword.filter(lang=lang)
                            if len(tkl) > 0:
                                tkl_ids = ",".join(map(str, tkl.values_list("id", flat=True)))
                                tkeywords_list += f",{tkl_ids}" if len(tkeywords_list) > 0 else tkl_ids
                    except Exception:
                        tb = traceback.format_exc()
                        logger.error(tb)

            tkeywords_form = TKeywordForm(instance=map_obj)
        else:
            tkeywords_form = ThesaurusAvailableForm(prefix="tkeywords")
            #  set initial values for thesaurus form
            for tid in tkeywords_form.fields:
                values = []
                values = [keyword.id for keyword in topic_thesaurus if int(tid) == keyword.thesaurus.id]
                tkeywords_form.fields[tid].initial = values

    if request.method == "POST" and map_form.is_valid() and category_form.is_valid() and tkeywords_form.is_valid():
        new_keywords = current_keywords if request.keyword_readonly else map_form.cleaned_data["keywords"]
        new_regions = map_form.cleaned_data["regions"]
        new_title = map_form.cleaned_data["title"]
        new_abstract = map_form.cleaned_data["abstract"]

        new_category = None
        if (
            category_form
            and "category_choice_field" in category_form.cleaned_data
            and category_form.cleaned_data["category_choice_field"]
        ):
            new_category = TopicCategory.objects.get(id=int(category_form.cleaned_data["category_choice_field"]))

        # update contact roles
        map_obj.set_contact_roles_from_metadata_edit(map_form)
        map_obj.save()

        map_obj.title = new_title
        map_obj.abstract = new_abstract
        map_obj.keywords.clear()
        map_obj.keywords.add(*new_keywords)
        map_obj.regions.clear()
        map_obj.regions.add(*new_regions)
        map_obj.category = new_category

        # clearing old metadata from the resource
        map_obj.metadata.all().delete()
        # creating new metadata for the resource
        for _m in json.loads(map_form.cleaned_data["extra_metadata"]):
            new_m = ExtraMetadata.objects.create(resource=map_obj, metadata=_m)
            map_obj.metadata.add(new_m)

        map_form.save_linked_resources()

        register_event(request, EventType.EVENT_CHANGE_METADATA, map_obj)
        if not ajax:
            return HttpResponseRedirect(hookset.map_detail_url(map_obj))

        message = map_obj.id

        try:
            # Keywords from THESAURUS management
            # Rewritten to work with updated autocomplete
            if not tkeywords_form.is_valid():
                return HttpResponse(json.dumps({"message": "Invalid thesaurus keywords"}, status_code=400))

            thesaurus_setting = getattr(settings, "THESAURUS", None)
            if thesaurus_setting:
                tkeywords_data = tkeywords_form.cleaned_data["tkeywords"]
                tkeywords_data = tkeywords_data.filter(thesaurus__identifier=thesaurus_setting["name"])
                map_obj.tkeywords.set(tkeywords_data)
            elif Thesaurus.objects.all().exists():
                fields = tkeywords_form.cleaned_data
                map_obj.tkeywords.set(tkeywords_form.cleanx(fields))

        except Exception:
            tb = traceback.format_exc()
            logger.error(tb)

        vals = {}
        if "group" in map_form.changed_data:
            vals["group"] = map_form.cleaned_data.get("group")
        if any([x in map_form.changed_data for x in ["is_approved", "is_published"]]):
            vals["is_approved"] = map_form.cleaned_data.get("is_approved", map_obj.is_approved)
            vals["is_published"] = map_form.cleaned_data.get("is_published", map_obj.is_published)
        resource_manager.update(
            map_obj.uuid,
            instance=map_obj,
            notify=True,
            vals=vals,
            extra_metadata=json.loads(map_form.cleaned_data["extra_metadata"]),
        )
        return HttpResponse(json.dumps({"message": message}))
    elif request.method == "POST" and (
        not map_form.is_valid() or not category_form.is_valid() or not tkeywords_form.is_valid()
    ):
        errors_list = {**map_form.errors.as_data(), **category_form.errors.as_data(), **tkeywords_form.errors.as_data()}
        logger.error(f"GeoApp Metadata form is not valid: {errors_list}")
        out = {"success": False, "errors": [f"{x}: {y[0].messages[0]}" for x, y in errors_list.items()]}
        return HttpResponse(json.dumps(out), content_type="application/json", status=400)
    # - POST Request Ends here -

    # Request.GET
    # define contact role forms
    contact_role_forms_context = {}
    for role in map_obj.get_multivalue_role_property_names():
        map_form.fields[role].initial = [p.username for p in map_obj.__getattribute__(role)]
        role_form = ProfileForm(prefix=role)
        role_form.hidden = True
        contact_role_forms_context[f"{role}_form"] = role_form

    layers = MapLayer.objects.filter(map=map_obj.id)
    metadata_author_groups = get_user_visible_groups(request.user)

    if not request.user.can_publish(map_obj):
        map_form.fields["is_published"].widget.attrs.update({"disabled": "true"})
    if not request.user.can_approve(map_obj):
        map_form.fields["is_approved"].widget.attrs.update({"disabled": "true"})

    register_event(request, EventType.EVENT_VIEW_METADATA, map_obj)
    return render(
        request,
        template,
        context={
            "resource": map_obj,
            "map": map_obj,
            "config": json.dumps(map_obj.blob),
            "panel_template": panel_template,
            "custom_metadata": custom_metadata,
            "map_form": map_form,
            "category_form": category_form,
            "tkeywords_form": tkeywords_form,
            "layers": layers,
            "preview": getattr(settings, "GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY", "mapstore"),
            "crs": getattr(settings, "DEFAULT_MAP_CRS", "EPSG:3857"),
            "metadata_author_groups": metadata_author_groups,
            "TOPICCATEGORY_MANDATORY": getattr(settings, "TOPICCATEGORY_MANDATORY", False),
            "GROUP_MANDATORY_RESOURCES": getattr(settings, "GROUP_MANDATORY_RESOURCES", False),
            "UI_MANDATORY_FIELDS": list(
                set(getattr(settings, "UI_DEFAULT_MANDATORY_FIELDS", []))
                | set(getattr(settings, "UI_REQUIRED_FIELDS", []))
            ),
            **contact_role_forms_context,
            "UI_ROLES_IN_TOGGLE_VIEW": map_obj.get_ui_toggled_role_property_names(),
        },
    )


@login_required
def map_metadata_advanced(request, mapid):
    return map_metadata(request, mapid, template="maps/map_metadata_advanced.html")


@xframe_options_exempt
def map_embed(request, mapid=None, template="maps/map_embed.html"):
    try:
        map_obj = _resolve_map(request, mapid, "base.view_resourcebase", _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(MSG_NOT_ALLOWED, status=403)
    except Exception:
        raise Http404(MSG_NOT_FOUND)

    if not map_obj:
        raise Http404(MSG_NOT_FOUND)

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    context_dict = {
        "access_token": access_token,
        "resource": map_obj,
    }

    register_event(request, EventType.EVENT_VIEW, map_obj)
    return render(request, template, context=context_dict)


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
            "authorizedRoles",
        ]
        for config_item in config_extras:
            if config_item in config:
                del config[config_item]
            if config_item in config["map"]:
                del config["map"][config_item]
        return json.dumps(config)
    else:
        return conf


# MAPS DOWNLOAD #


def map_download(request, mapid, template="maps/map_download.html"):
    """
    Download all the layers of a map as a batch
    XXX To do, remove layer status once progress id done
    This should be fix because
    """
    try:
        map_obj = _resolve_map(request, mapid, "base.download_resourcebase", _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(MSG_NOT_ALLOWED, status=403)
    except Exception:
        raise Http404(MSG_NOT_FOUND)
    if not map_obj:
        raise Http404(MSG_NOT_FOUND)

    map_status = dict()
    if request.method == "POST":

        def perm_filter(layer):
            return request.user.has_perm("base.view_resourcebase", obj=layer.get_self_resource())

        mapJson = map_obj.json(perm_filter)

        # we need to remove duplicate layers
        j_map = json.loads(mapJson)
        j_datasets = j_map["layers"]
        for j_dataset in j_datasets:
            if j_dataset["service"] is None:
                j_datasets.remove(j_dataset)
                continue
            if (len([_l for _l in j_datasets if _l == j_dataset])) > 1:
                j_datasets.remove(j_dataset)
        mapJson = json.dumps(j_map)

        # the path to geoserver backend continue here
        url = urljoin(settings.SITEURL, reverse("download-map", kwargs={"mapid": mapid}))
        resp, content = http_client.request(url, "POST", data=mapJson)

        status = int(resp.status_code)

        if status == 200:
            map_status = json.loads(content)
            request.session["map_status"] = map_status
        else:
            raise Exception(f"Could not start the download of {map_obj.title}. Error was: {content}")

    locked_datasets = []
    remote_datasets = []
    downloadable_datasets = []

    for lyr in map_obj.maplayers.iterator():
        if lyr.group != "background":
            if not lyr.local:
                remote_datasets.append(lyr)
            else:
                ownable_dataset = Dataset.objects.get(alternate=lyr.name)
                if not request.user.has_perm("download_resourcebase", obj=ownable_dataset.get_self_resource()):
                    locked_datasets.append(lyr)
                else:
                    # we need to add the layer only once
                    if len([_l for _l in downloadable_datasets if _l.name == lyr.name]) == 0:
                        downloadable_datasets.append(lyr)
    site_url = settings.SITEURL.rstrip("/") if settings.SITEURL.startswith("http") else settings.SITEURL

    register_event(request, EventType.EVENT_DOWNLOAD, map_obj)

    return render(
        request,
        template,
        context={
            "geoserver": ogc_server_settings.PUBLIC_LOCATION,
            "map_status": map_status,
            "map": map_obj,
            "locked_datasets": locked_datasets,
            "remote_datasets": remote_datasets,
            "downloadable_datasets": downloadable_datasets,
            "site": site_url,
        },
    )


def map_wmc(request, mapid, template="maps/wmc.xml"):
    """Serialize an OGC Web Map Context Document (WMC) 1.1"""
    try:
        map_obj = _resolve_map(request, mapid, "base.view_resourcebase", _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(MSG_NOT_ALLOWED, status=403)
    except Exception:
        raise Http404(MSG_NOT_FOUND)
    if not map_obj:
        raise Http404(MSG_NOT_FOUND)

    site_url = settings.SITEURL.rstrip("/") if settings.SITEURL.startswith("http") else settings.SITEURL
    return render(
        request,
        template,
        context={
            "map": map_obj,
            "maplayers": map_obj.maplayers.all(),
            "siteurl": site_url,
        },
        content_type="text/xml",
    )


@deprecated(version="2.10.1", reason="APIs have been changed on geospatial service")
def map_wms(request, mapid):
    """
    Publish local map layers as group layer in local OWS.

    /maps/:id/wms

    GET: return endpoint information for group layer,
    PUT: update existing or create new group layer.
    """
    try:
        map_obj = _resolve_map(request, mapid, "base.view_resourcebase", _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(MSG_NOT_ALLOWED, status=403)
    except Exception:
        raise Http404(MSG_NOT_FOUND)
    if not map_obj:
        raise Http404(MSG_NOT_FOUND)

    if request.method == "PUT":
        try:
            layerGroupName = map_obj.publish_dataset_group()
            response = dict(
                layerGroupName=layerGroupName,
                ows=getattr(ogc_server_settings, "ows", ""),
            )
            register_event(request, EventType.EVENT_PUBLISH, map_obj)
            return HttpResponse(json.dumps(response), content_type="application/json")
        except Exception:
            return HttpResponseServerError()

    if request.method == "GET":
        response = dict(
            layerGroupName=getattr(map_obj.dataset_group, "name", ""),
            ows=getattr(ogc_server_settings, "ows", ""),
        )
        return HttpResponse(json.dumps(response), content_type="application/json")

    return HttpResponseNotAllowed(["PUT", "GET"])


def mapdataset_attributes(request, layername):
    # Return custom layer attribute labels/order in JSON format
    layer = Dataset.objects.get(alternate=layername)
    return HttpResponse(json.dumps(layer.attribute_config()), content_type="application/json")


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


def ajax_url_lookup(request):
    if request.method != "POST":
        return HttpResponse(content="ajax user lookup requires HTTP POST", status=405, content_type="text/plain")
    elif "query" not in request.POST:
        return HttpResponse(
            content='use a field named "query" to specify a prefix to filter urls', content_type="text/plain"
        )
    if request.POST["query"] != "":
        maps = Map.objects.filter(urlsuffix__startswith=request.POST["query"])
        if request.POST["mapid"] != "":
            maps = maps.exclude(id=request.POST["mapid"])
        json_dict = {
            "urls": [({"url": m.urlsuffix}) for m in maps],
            "count": maps.count(),
        }
    else:
        json_dict = {
            "urls": [],
            "count": 0,
        }
    return HttpResponse(content=json.dumps(json_dict), content_type="text/plain")


def map_metadata_detail(request, mapid, template="maps/map_metadata_detail.html", custom_metadata=None):
    try:
        map_obj = _resolve_map(request, mapid, "view_resourcebase")
    except PermissionDenied:
        return HttpResponse(MSG_NOT_ALLOWED, status=403)
    except Exception:
        raise Http404(MSG_NOT_FOUND)
    if not map_obj:
        raise Http404(MSG_NOT_FOUND)

    group = None
    if map_obj.group:
        try:
            group = GroupProfile.objects.get(slug=map_obj.group.name)
        except GroupProfile.DoesNotExist:
            group = None
    site_url = settings.SITEURL.rstrip("/") if settings.SITEURL.startswith("http") else settings.SITEURL
    register_event(request, EventType.EVENT_VIEW_METADATA, map_obj)

    return render(
        request,
        template,
        context={"resource": map_obj, "group": group, "SITEURL": site_url, "custom_metadata": custom_metadata},
    )


@login_required
def map_batch_metadata(request):
    return batch_modify(request, "Map")
