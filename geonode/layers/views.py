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
import decimal
import logging
import traceback

from owslib.wfs import WebFeatureService

from django.conf import settings

from django.http import Http404
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.clickjacking import xframe_options_exempt

from geonode import geoserver
from geonode.base.auth import get_or_create_token
from geonode.layers.models import Dataset
from geonode.layers.utils import (
    get_default_dataset_download_handler,
)
from geonode.services.models import Service
from geonode.base import register_event
from geonode.utils import check_ogc_backend, resolve_object
from geonode.geoserver.helpers import ogc_server_settings

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    from geonode.geoserver.helpers import gs_catalog

CONTEXT_LOG_FILE = ogc_server_settings.LOG_FILE

logger = logging.getLogger("geonode.layers.views")

METADATA_UPLOADED_PRESERVE_ERROR = _(
    "Note: this dataset's orginal metadata was \
populated and preserved by importing a metadata XML file. This metadata cannot be edited."
)

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this dataset")
_PERMISSION_MSG_GENERIC = _("You do not have permissions for this dataset.")
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this dataset")
_PERMISSION_MSG_METADATA = _("You are not permitted to modify this dataset's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this dataset")


def _resolve_dataset(request, alternate, permission="base.view_resourcebase", msg=_PERMISSION_MSG_GENERIC, **kwargs):
    """
    Resolve the layer by the provided typename (which may include service name) and check the optional permission.
    """
    service_typename = alternate.split(":", 1)
    for _s in Service.objects.filter(name__startswith=service_typename[0]):
        query = {
            "alternate": service_typename[1],
            "remote_service": _s,
        }
        try:
            return resolve_object(request, Dataset, query, permission=permission, permission_msg=msg, **kwargs)
        except (Dataset.DoesNotExist, Http404) as e:
            logger.debug(e)
    if len(service_typename) > 1 and ":" in service_typename[1]:
        if service_typename[0]:
            query = {"store": service_typename[0], "alternate": service_typename[1]}
        else:
            query = {"alternate": service_typename[1]}
    else:
        query = {"alternate": alternate}
    test_query = Dataset.objects.filter(**query)
    if test_query.count() > 1 and test_query.exclude(subtype="remote").count() == 1:
        query = {"id": test_query.exclude(subtype="remote").last().id}
    elif test_query.count() > 1:
        query = {"id": test_query.last().id}
    return resolve_object(request, Dataset, query, permission=permission, permission_msg=msg, **kwargs)


# Loads the data using the OWS lib when the "Do you want to filter it"
# button is clicked.
def load_dataset_data(request):
    context_dict = {}
    data_dict = json.loads(request.POST.get("json_data"))
    layername = data_dict["dataset_name"]
    filtered_attributes = ""
    if not isinstance(data_dict["filtered_attributes"], str):
        filtered_attributes = [x for x in data_dict["filtered_attributes"] if "/load_dataset_data" not in x]
    name = layername if ":" not in layername else layername.split(":")[1]
    location = f"{(settings.OGC_SERVER['default']['LOCATION'])}wms"
    headers = {}
    if request and "access_token" in request.session:
        access_token = request.session["access_token"]
        headers["Authorization"] = f"Bearer {access_token}"

    try:
        wfs = WebFeatureService(location, version="1.1.0", headers=headers)
        response = wfs.getfeature(typename=name, propertyname=filtered_attributes, outputFormat="application/json")
        x = response.read()
        x = json.loads(x)
        features_response = json.dumps(x)
        decoded = json.loads(features_response)
        decoded_features = decoded["features"]
        properties = {}
        for key in decoded_features[0]["properties"]:
            properties[key] = []

        # loop the dictionary based on the values on the list and add the properties
        # in the dictionary (if doesn't exist) together with the value
        from collections.abc import Iterable

        for i in range(len(decoded_features)):
            for key, value in decoded_features[i]["properties"].items():
                if (
                    value != ""
                    and isinstance(value, (str, int, float))
                    and ((isinstance(value, Iterable) and "/load_dataset_data" not in value) or value)
                ):
                    properties[key].append(value)

        for key in properties:
            properties[key] = list(set(properties[key]))
            properties[key].sort()

        context_dict["feature_properties"] = properties
    except Exception:
        traceback.print_exc()
        logger.error("Possible error with OWSLib.")
    return HttpResponse(json.dumps(context_dict), content_type="application/json")


def dataset_feature_catalogue(request, layername, template="../../catalogue/templates/catalogue/feature_catalogue.xml"):
    try:
        layer = _resolve_dataset(request, layername)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    if layer.subtype != "vector":
        out = {"success": False, "errors": "layer is not a feature type"}
        return HttpResponse(json.dumps(out), content_type="application/json", status=400)

    attributes = []

    for attrset in layer.attribute_set.order_by("display_order"):
        attr = {"name": attrset.attribute, "type": attrset.attribute_type}
        attributes.append(attr)

    context_dict = {
        "dataset": layer,
        "attributes": attributes,
        "metadata": settings.PYCSW["CONFIGURATION"]["metadata:main"],
    }
    register_event(request, "view", layer)
    return render(request, template, context=context_dict, content_type="application/xml")


@csrf_exempt
def dataset_download(request, layername):
    handler = get_default_dataset_download_handler()
    return handler(request, layername).get_download_response()


@login_required
def dataset_granule_remove(request, granule_id, layername, template="datasets/dataset_granule_remove.html"):
    try:
        layer = _resolve_dataset(request, layername, "base.delete_resourcebase", _PERMISSION_MSG_DELETE)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    if request.method == "GET":
        return render(request, template, context={"granule_id": granule_id, "dataset": layer})
    if request.method == "POST":
        try:
            cat = gs_catalog
            cat._cache.clear()
            store = cat.get_store(layer.name)
            coverages = cat.mosaic_coverages(store)
            cat.mosaic_delete_granule(coverages["coverages"]["coverage"][0]["name"], store, granule_id)
        except Exception as e:
            traceback.print_exc()
            message = f'{_("Unable to delete layer")}: {layer.alternate}.'
            if "referenced by layer group" in getattr(e, "message", ""):
                message = _(
                    "This dataset is a member of a layer group, you must remove the dataset from the group "
                    "before deleting."
                )

            messages.error(request, message)
            return render(request, template, context={"layer": layer})
        return HttpResponseRedirect(layer.get_absolute_url())
    else:
        return HttpResponse("Not allowed", status=403)


def get_dataset(request, layername):
    """Get Dataset object as JSON"""

    # Function to treat Decimal in json.dumps.
    # http://stackoverflow.com/a/16957370/1198772
    def decimal_default(obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        raise TypeError

    logger.debug("Call get layer")
    if request.method == "GET":
        try:
            dataset_obj = _resolve_dataset(request, layername)
        except PermissionDenied:
            return HttpResponse(_("Not allowed"), status=403)
        except Exception:
            raise Http404(_("Not found"))
        if not dataset_obj:
            raise Http404(_("Not found"))

        logger.debug(layername)
        response = {
            "typename": layername,
            "name": dataset_obj.name,
            "title": dataset_obj.title,
            "url": dataset_obj.get_tiles_url(),
            "bbox_string": dataset_obj.bbox_string,
            "bbox_x0": dataset_obj.bbox_helper.xmin,
            "bbox_x1": dataset_obj.bbox_helper.xmax,
            "bbox_y0": dataset_obj.bbox_helper.ymin,
            "bbox_y1": dataset_obj.bbox_helper.ymax,
        }
        return HttpResponse(
            json.dumps(response, ensure_ascii=False, default=decimal_default), content_type="application/javascript"
        )


@xframe_options_exempt
def dataset_embed(request, layername):
    try:
        layer = _resolve_dataset(request, layername, "base.view_resourcebase", _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    layer.view_count_up(request.user)

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    context_dict = {
        "access_token": access_token,
        "resource": layer,
    }
    return TemplateResponse(request, "datasets/dataset_embed.html", context=context_dict)


def dataset_view_counter(dataset_id, viewer):
    _l = Dataset.objects.get(id=dataset_id)
    _u = get_user_model().objects.get(username=viewer)
    _l.view_count_up(_u, do_local=True)
