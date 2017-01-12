import os
import sys
import shutil
import traceback
import datetime
import time
import csv
from urlparse import parse_qs

from crispy_forms.utils import render_crispy_form

from django.conf import settings
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import (
    redirect, get_object_or_404, render, render_to_response)
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.template.response import TemplateResponse
from django.utils import dateformat
from django.utils import timezone
from django.utils import simplejson as json
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from geonode.base.enumerations import CHARSETS
from geonode.cephgeo.models import UserJurisdiction
from geonode.documents.models import get_related_documents
from geonode.documents.models import Document
from geonode.layers.models import UploadSession, Style
from geonode.layers.utils import file_upload
from geonode.people.models import Profile
from geonode.people.views import profile_detail
from geonode.security.views import _perms_info_json
from geonode.tasks.jurisdiction import place_name_update, jurisdiction_style
from geonode.tasks.jurisdiction2 import compute_size_update, assign_grid_refs, assign_grid_refs_all
from geonode.utils import default_map_config
from geonode.utils import GXPLayer
from geonode.utils import GXPMap
from geonode.utils import llbbox_to_mercator
from geonode.utils import build_social_links

from geoserver.catalog import Catalog

from unidecode import unidecode
from pprint import pprint


from braces.views import (
    SuperuserRequiredMixin, LoginRequiredMixin,
)

from geonode.datarequests.forms import (
    ProfileRequestForm, DataRequestShapefileForm,
    RejectionForm, DataRequestForm)

from geonode.datarequests.models import DataRequestProfile, DataRequest, ProfileRequest

from geonode.datarequests.utils import (
    get_place_name, get_area_coverage)

@login_required
def requests_landing(request):
    if request.user.is_superuser:
        return TemplateResponse(request, 'datarequests/requests_landing.html',{}, status=200).render()
    else:
        return HttpResponseRedirect(reverse('datarequests:data_request_browse'))

@login_required
def requests_csv(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect("/forbidden")
    else:
        response = HttpResponse(content_type='text/csv')
        datetoday = timezone.now()
        response['Content-Disposition'] = 'attachment; filename="requests-"'+str(datetoday.month)+str(datetoday.day)+str(datetoday.year)+'.csv"'

        writer = csv.writer(response)
        header_fields = ['name','email','contact_number', 'organization', 'organization_type','organization_other', 'created','status','has_data_request','data_request_status','area_coverage','estimated_data_size', ]
        writer.writerow(header_fields)

        objects = ProfileRequest.objects.all().order_by('pk')
        
        profile_request_fields = ['name','email','contact_number', 'organization', 'organization_type','organization_other', 'created','status', 'has_data_request','data_request_status','area_coverage','estimated_data_size']

        for o in objects:
            writer.writerow(o.to_values_list(profile_request_fields))
            
        objects = DataRequest.objects.filter(profile_request = None).order_by('pk')
        
        data_request_fields = ['name', 'email', 'organization','organization_type','organization_other','created','profile_request_status','has_data_request','status','area_coverage','estimated_data_size']
        
        for o in objects:
            writer.writerow(o.to_values_list(data_request_fields))

        return response
    

class DataRequestProfileList(LoginRequiredMixin, TemplateView):
    template_name = 'datarequests/old_requests_model_list.html'
    raise_exception = True

@login_required
def old_request_detail(request, pk,template="datarequests/old_request_detail.html"):
    if not request.user.is_superuser:
        return HttpResponseRedirect("/forbidden")
        
    request_profile = get_object_or_404(DataRequestProfile, pk=pk)

    if not request.user.is_superuser and not request_profile.profile == request.user:
        raise PermissionDenied

    context_dict={"request_profile": request_profile}

    if request_profile.jurisdiction_shapefile:
        layer = request_profile.jurisdiction_shapefile
        # assert False, str(layer_bbox)
        config = layer.attribute_config()
        # Add required parameters for GXP lazy-loading
        layer_bbox = layer.bbox
        bbox = [float(coord) for coord in list(layer_bbox[0:4])]
        srid = layer.srid

        # Transform WGS84 to Mercator.
        config["srs"] = srid if srid != "EPSG:4326" else "EPSG:900913"
        config["bbox"] = llbbox_to_mercator([float(coord) for coord in bbox])

        config["title"] = layer.title
        config["queryable"] = True

        if layer.storeType == "remoteStore":
            service = layer.service
            source_params = {
                "ptype": service.ptype,
                "remote": True,
                "url": service.base_url,
                "name": service.name}
            maplayer = GXPLayer(
                name=layer.typename,
                ows_url=layer.ows_url,
                layer_params=json.dumps(config),
                source_params=json.dumps(source_params))
        else:
            maplayer = GXPLayer(
                name=layer.typename,
                ows_url=layer.ows_url,
                layer_params=json.dumps(config))

        # center/zoom don't matter; the viewer will center on the layer bounds
        map_obj = GXPMap(projection="EPSG:900913")
        NON_WMS_BASE_LAYERS = [
            la for la in default_map_config()[1] if la.ows_url is None]

        metadata = layer.link_set.metadata().filter(
            name__in=settings.DOWNLOAD_FORMATS_METADATA)

        context_dict ["resource"] = layer
        context_dict ["permissions_json"] = _perms_info_json(layer)
        context_dict ["documents"] = get_related_documents(layer)
        context_dict ["metadata"] =  metadata
        context_dict ["is_layer"] = True
        context_dict ["wps_enabled"] = settings.OGC_SERVER['default']['WPS_ENABLED'],

        context_dict["viewer"] = json.dumps(
            map_obj.viewer_json(request.user, * (NON_WMS_BASE_LAYERS + [maplayer])))
        context_dict["preview"] = getattr(
            settings,
            'LAYER_PREVIEW_LIBRARY',
            'leaflet')

        if request.user.has_perm('download_resourcebase', layer.get_self_resource()):
            if layer.storeType == 'dataStore':
                links = layer.link_set.download().filter(
                    name__in=settings.DOWNLOAD_FORMATS_VECTOR)
            else:
                links = layer.link_set.download().filter(
                    name__in=settings.DOWNLOAD_FORMATS_RASTER)
            context_dict["links"] = links

        if settings.SOCIAL_ORIGINS:
            context_dict["social_links"] = build_social_links(request, layer)

    context_dict["request_reject_form"]= DataRequestProfileRejectForm(instance=request_profile)

    return render_to_response(template, RequestContext(request, context_dict))


@login_required
def old_request_migration(request, pk)
    raise Http404
