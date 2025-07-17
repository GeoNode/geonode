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

from django.conf import settings

from django.http import Http404
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt

from geonode.base.auth import get_or_create_token
from geonode.layers.models import Dataset
from geonode.layers.utils import (
    get_default_dataset_download_handler,
)
from geonode.services.models import Service
from geonode.base import register_event
from geonode.utils import resolve_object
from geonode.geoserver.helpers import ogc_server_settings

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
        "metadata": settings.PYCSW["CONFIGURATION"]["metadata"],
    }
    register_event(request, "view", layer)
    return render(request, template, context=context_dict, content_type="application/xml")


@csrf_exempt
def dataset_download(request, layername):
    handler = get_default_dataset_download_handler()
    return handler(request, layername).get_download_response()


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
