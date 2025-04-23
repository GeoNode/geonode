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
from urllib.parse import urljoin

from deprecated import deprecated
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseNotAllowed, HttpResponseServerError
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_exempt

from geonode import geoserver
from geonode.base import register_event
from geonode.base.auth import get_or_create_token
from geonode.base.enumerations import EventType
from geonode.layers.models import Dataset
from geonode.maps.contants import (
    _PERMISSION_MSG_GENERIC,
    _PERMISSION_MSG_VIEW,
    MSG_NOT_ALLOWED,
    MSG_NOT_FOUND,
)
from geonode.maps.models import Map
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
