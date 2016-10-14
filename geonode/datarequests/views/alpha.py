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

from .forms import (
    DataRequestProfileForm, DataRequestProfileShapefileForm,
    DataRequestProfileRejectForm, DataRequestDetailsForm,
    DataRequestInfoForm, DataRequestProjectForm, DataRequestShapefileForm)
from .models import DataRequestProfile, DataRequest, ProfileRequest
from .utils import (
    get_place_name, get_area_coverage)


class ProfileRequestList(LoginRequiredMixin, TemplateView):
    template_name = 'datarequests/profile_request_list.html'
    raise_exception = True

class DataRequestList(LoginRequiredMixin, TemplateView):
    template_name = 'datarequests/data_request_list.html'
    raise_exception = True

@login_required
def requests_landing(request):
    if request.user.is_superuser:
        return TemplateResponse(request, 'datarequests/requests_landing.html',{}, status=200).render()
    else:
        return HttpResponseRedirect(reverse('datarequests:data_request_browse'))

@login_required
def data_request_csv(request):
    if not request.user.is_superuser:
        raise HttpResponseForbidden

    response = HttpResponse(content_type='text/csv')
    datetoday = timezone.now()
    response['Content-Disposition'] = 'attachment; filename="datarequests-"'+str(datetoday.month)+str(datetoday.day)+str(datetoday.year)+'.csv"'

    writer = csv.writer(response)
    fields = ['id','name','email','contact_number', 'organization', 'organization_type','organization_other','has_letter','has_shapefile','project_summary', 'created','request_status', 'date of action','rejection_reason','juris_data_size','area_coverage']
    writer.writerow( fields)

    objects = DataRequestProfile.objects.all().order_by('pk')

    for o in objects:
        writer.writerow(o.to_values_list(fields))

    return response

def profile_request_detail(request, pk, template='datarequests/profile_detail.html'):

    request_profile = get_object_or_404(ProfileRequest, pk=pk)

    if not request.user.is_superuser and not request_profile.profile == request.user:
        raise PermissionDenied


    #if not request_profile.date:
    #    raise Http404

    context_dict={"request_profile": request_profile}

    # if request_profile.jurisdiction_shapefile:
    #     layer = request_profile.jurisdiction_shapefile
    #     # assert False, str(layer_bbox)
    #     config = layer.attribute_config()
    #     # Add required parameters for GXP lazy-loading
    #     layer_bbox = layer.bbox
    #     bbox = [float(coord) for coord in list(layer_bbox[0:4])]
    #     srid = layer.srid
    #
    #     # Transform WGS84 to Mercator.
    #     config["srs"] = srid if srid != "EPSG:4326" else "EPSG:900913"
    #     config["bbox"] = llbbox_to_mercator([float(coord) for coord in bbox])
    #
    #     config["title"] = layer.title
    #     config["queryable"] = True
    #
    #     if layer.storeType == "remoteStore":
    #         service = layer.service
    #         source_params = {
    #             "ptype": service.ptype,
    #             "remote": True,
    #             "url": service.base_url,
    #             "name": service.name}
    #         maplayer = GXPLayer(
    #             name=layer.typename,
    #             ows_url=layer.ows_url,
    #             layer_params=json.dumps(config),
    #             source_params=json.dumps(source_params))
    #     else:
    #         maplayer = GXPLayer(
    #             name=layer.typename,
    #             ows_url=layer.ows_url,
    #             layer_params=json.dumps(config))
    #
    #     # center/zoom don't matter; the viewer will center on the layer bounds
    #     map_obj = GXPMap(projection="EPSG:900913")
    #     NON_WMS_BASE_LAYERS = [
    #         la for la in default_map_config()[1] if la.ows_url is None]
    #
    #     metadata = layer.link_set.metadata().filter(
    #         name__in=settings.DOWNLOAD_FORMATS_METADATA)
    #
    #     context_dict ["resource"] = layer
    #     context_dict ["permissions_json"] = _perms_info_json(layer)
    #     context_dict ["documents"] = get_related_documents(layer)
    #     context_dict ["metadata"] =  metadata
    #     context_dict ["is_layer"] = True
    #     context_dict ["wps_enabled"] = settings.OGC_SERVER['default']['WPS_ENABLED'],
    #
    #     context_dict["viewer"] = json.dumps(
    #         map_obj.viewer_json(request.user, * (NON_WMS_BASE_LAYERS + [maplayer])))
    #     context_dict["preview"] = getattr(
    #         settings,
    #         'LAYER_PREVIEW_LIBRARY',
    #         'leaflet')
    #
    #     if request.user.has_perm('download_resourcebase', layer.get_self_resource()):
    #         if layer.storeType == 'dataStore':
    #             links = layer.link_set.download().filter(
    #                 name__in=settings.DOWNLOAD_FORMATS_VECTOR)
    #         else:
    #             links = layer.link_set.download().filter(
    #                 name__in=settings.DOWNLOAD_FORMATS_RASTER)
    #         context_dict["links"] = links
    #
    #     if settings.SOCIAL_ORIGINS:
    #         context_dict["social_links"] = build_social_links(request, layer)

    context_dict["request_reject_form"]= DataRequestProfileRejectForm(instance=request_profile)

    return render_to_response(template, RequestContext(request, context_dict))


def data_request_profile_reject(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied

    if not request.method == 'POST':
        raise PermissionDenied

    request_profile = get_object_or_404(ProfileRequest, pk=pk)

    if request_profile.request_status == 'pending':
        form = parse_qs(request.POST.get('form', None))
        request_profile.rejection_reason = form['rejection_reason'][0]
        request_profile.request_status = 'rejected'
        if 'additional_rejection_reason' in form.keys():
            request_profile.additional_rejection_reason = form['additional_rejection_reason'][0]
        request_profile.administrator = request.user
        request_profile.action_date = timezone.now()
        request_profile.save()
        if request_profile.profile:
            pprint("sending request rejection email")
            request_profile.send_request_rejection_email()
        else:
            pprint("sending account rejection email")
            request_profile.send_account_rejection_email()

    url = request.build_absolute_uri(request_profile.get_absolute_url())

    return HttpResponse(
        json.dumps({
            'result': 'success',
            'errors': '',
            'url': url}),
        status=200,
        mimetype='text/plain'
    )

def data_request_profile_cancel(request, pk):
    request_profile = get_object_or_404(ProfileRequest, pk=pk)

    if not request.user.is_superuser and  not request_profile.profile == request.user:
        raise PermissionDenied

    if not request.method == 'POST':
        raise PermissionDenied

    request_profile = get_object_or_404(ProfileRequest, pk=pk)

    if request_profile.request_status == 'pending' or request_profile.request_status == 'unconfirmed':
        pprint("Yown pasok")
        form = request.POST.get('form', None)
        request_profile.request_status = 'cancelled'
        if form:
            form_parsed = parse_qs(request.POST.get('form', None))
            if 'rejection_reason' in form_parsed.keys():
                request_profile.rejection_reason = form_parsed['rejection_reason'][0]

            if 'additional_rejection_reason' in form_parsed.keys():
                request_profile.additional_rejection_reason = form_parsed['additional_rejection_reason'][0]

        request_profile.administrator = request.user
        request_profile.action_date = timezone.now()
        request_profile.save()

    url = request.build_absolute_uri(request_profile.get_absolute_url())
    if request.user.is_superuser:
        return HttpResponse(
            json.dumps({
                'result': 'success',
                'errors': '',
                'url': url}),
            status=200,
            mimetype='text/plain'
        )
    else:
        return HttpResponseRedirect(reverse('datarequests:data_request_profile', args=[pk]))

def data_request_profile_approve(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied
    if not request.method == 'POST':
        raise PermissionDenied

    if request.method == 'POST':
        request_profile = get_object_or_404(ProfileRequest, pk=pk)

        if not request_profile.has_verified_email or request_profile.request_status != 'pending':
            raise PermissionDenied

        result = True
        message = ''
        is_new_acc=True

        if not request_profile.profile or not request_profile.username or not request_profile.ftp_folder:
            result, message = request_profile.create_account() #creates account in AD if AD profile does not exist
        else:
            is_new_acc = False

        if not result:
            messages.error (request, _(message))
        else:
            request_profile.profile.organization_type = request_profile.organization_type
            request_profile.profile.organization_other = request_profile.organization_other
            request_profile.profile.save()

            if request_profile.jurisdiction_shapefile:
                request_profile.assign_jurisdiction() #assigns/creates jurisdiction object
                #place_name_update.delay([request_profile])
                #compute_size_update.delay([request_profile])
                assign_grid_refs.delay(request_profile.profile)
            else:
                try:
                    uj = UserJurisdiction.objects.get(user=request_profile.profile)
                    uj.delete()
                except ObjectDoesNotExist as e:
                    pprint("Jurisdiction Shapefile not found, nothing to delete. Carry on")

            request_profile.set_approved(is_new_acc)

        return HttpResponseRedirect(request_profile.get_absolute_url())

    else:
        return HttpResponseRedirect("/forbidden/")


def data_request_profile_reconfirm(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied

    if not request.method == 'POST':
        raise PermissionDenied

    if request.method == 'POST':
        request_profile = get_object_or_404(ProfileRequest, pk=pk)

        request_profile.send_verification_email()
        return HttpResponseRedirect(request_profile.get_absolute_url())

def data_request_profile_recreate_dir(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied

    if not request.method == 'POST':
        raise PermissionDenied

    if request.method == 'POST':
        request_profile = get_object_or_404(ProfileRequest, pk=pk)

        request_profile.create_directory()
        return HttpResponseRedirect(request_profile.get_absolute_url())

def data_request_compute_size(request):
    if request.user.is_superuser:
        data_requests = DataRequest.objects.exclude(jurisdiction_shapefile=None)
        compute_size_update.delay(data_requests)
        messages.info(request, "The estimated data size area coverage of the requests are currently being computed")
        return HttpResponseRedirect(reverse('datarequests:data_request_browse'))
    else:
        return HttpResponseRedirect('/forbidden/')


def data_request_profile_compute_size(request, pk):
    if request.user.is_superuser and request.method == 'POST':
        if DataRequest.objects.get(pk=pk).jurisdiction_shapefile:
            data_requests = DataRequest.objects.filter(pk=pk)
            compute_size_update.delay(data_requests)
            messages.info(request, "The estimated data size area coverage of the request is currently being computed")
        else:
            messages.info(request, "This request does not have a shape file")

        return HttpResponseRedirect(reverse('datarequests:data_request_browse'))
    else:
        return HttpResponseRedirect('/forbidden/')

def data_request_reverse_geocode(request):
    if request.user.is_superuser:
        data_requests = DataRequest.objects.exclude(jurisdiction_shapefile=None)
        place_name_update.delay(data_requests)
        messages.info(request,"Retrieving approximated place names of data requests")
        return HttpResponseRedirect(reverse('datarequests:data_request_browse'))
    else:
        return HttpResponseRedirect('/forbidden/')

def data_request_profile_reverse_geocode(request, pk):
    if request.user.is_superuser and request.method == 'POST':
        if DataRequest.objects.get(pk=pk).jurisdiction_shapefile:
            data_requests = DataRequest.objects.filter(pk=pk)
            place_name_update.delay(data_requests)
            messages.info(request, "Retrieving approximated place names of data request")
        else:
            messages.info(request, "This request does not have a shape file")

        return HttpResponseRedirect(reverse('datarequests:data_request_browse'))
    else:
        return HttpResponseRedirect('/forbidden/')
        
def data_request_assign_gridrefs(request):
    if request.user.is_superuser:
        assign_grid_refs_all.delay()
        messages.info(request, "Now processing jurisdictions. Please wait for a few minutes for them to finish")
        return HttpResponseRedirect(reverse('datarequests:data_request_browse'))
        
    else:
        return HttpResponseRedirect('/forbidden/')
            

def data_request_detail(request, pk, template='datarequests/data_detail.html'):

    request_profile = get_object_or_404(DataRequest, pk=pk)

    if not request.user.is_superuser and not request_profile.profile == request.user:
        raise PermissionDenied


    #if not request_profile.date:
    #    raise Http404

    context_dict={"request_profile": request_profile}

    # if request_profile.jurisdiction_shapefile:
    #     layer = request_profile.jurisdiction_shapefile
    #     # assert False, str(layer_bbox)
    #     config = layer.attribute_config()
    #     # Add required parameters for GXP lazy-loading
    #     layer_bbox = layer.bbox
    #     bbox = [float(coord) for coord in list(layer_bbox[0:4])]
    #     srid = layer.srid
    #
    #     # Transform WGS84 to Mercator.
    #     config["srs"] = srid if srid != "EPSG:4326" else "EPSG:900913"
    #     config["bbox"] = llbbox_to_mercator([float(coord) for coord in bbox])
    #
    #     config["title"] = layer.title
    #     config["queryable"] = True
    #
    #     if layer.storeType == "remoteStore":
    #         service = layer.service
    #         source_params = {
    #             "ptype": service.ptype,
    #             "remote": True,
    #             "url": service.base_url,
    #             "name": service.name}
    #         maplayer = GXPLayer(
    #             name=layer.typename,
    #             ows_url=layer.ows_url,
    #             layer_params=json.dumps(config),
    #             source_params=json.dumps(source_params))
    #     else:
    #         maplayer = GXPLayer(
    #             name=layer.typename,
    #             ows_url=layer.ows_url,
    #             layer_params=json.dumps(config))
    #
    #     # center/zoom don't matter; the viewer will center on the layer bounds
    #     map_obj = GXPMap(projection="EPSG:900913")
    #     NON_WMS_BASE_LAYERS = [
    #         la for la in default_map_config()[1] if la.ows_url is None]
    #
    #     metadata = layer.link_set.metadata().filter(
    #         name__in=settings.DOWNLOAD_FORMATS_METADATA)
    #
    #     context_dict ["resource"] = layer
    #     context_dict ["permissions_json"] = _perms_info_json(layer)
    #     context_dict ["documents"] = get_related_documents(layer)
    #     context_dict ["metadata"] =  metadata
    #     context_dict ["is_layer"] = True
    #     context_dict ["wps_enabled"] = settings.OGC_SERVER['default']['WPS_ENABLED'],
    #
    #     context_dict["viewer"] = json.dumps(
    #         map_obj.viewer_json(request.user, * (NON_WMS_BASE_LAYERS + [maplayer])))
    #     context_dict["preview"] = getattr(
    #         settings,
    #         'LAYER_PREVIEW_LIBRARY',
    #         'leaflet')
    #
    #     if request.user.has_perm('download_resourcebase', layer.get_self_resource()):
    #         if layer.storeType == 'dataStore':
    #             links = layer.link_set.download().filter(
    #                 name__in=settings.DOWNLOAD_FORMATS_VECTOR)
    #         else:
    #             links = layer.link_set.download().filter(
    #                 name__in=settings.DOWNLOAD_FORMATS_RASTER)
    #         context_dict["links"] = links
    #
    #     if settings.SOCIAL_ORIGINS:
    #         context_dict["social_links"] = build_social_links(request, layer)

    context_dict["request_reject_form"]= DataRequestProfileRejectForm(instance=request_profile)

    return render_to_response(template, RequestContext(request, context_dict))

def data_request_facet_count(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    if not request.method == 'POST':
        raise PermissionDenied

    facets_count = {
        'pending': ProfileRequest.objects.filter(
            request_status='pending').exclude(date=None).count(),
        'approved': ProfileRequest.objects.filter(
            request_status='approved').count(),
        'rejected': ProfileRequest.objects.filter(
            request_status='rejected').count(),
        'cancelled': ProfileRequest.objects.filter(
            request_status='cancelled').exclude(date=None).count(),
    }

    return HttpResponse(
        json.dumps(facets_count),
        status=200,
        mimetype='text/plain'
    )

def update_datarequest_obj(datarequest=None, parameter_dict=None, interest_layer=None, request_letter = None):
    if datarequest is None or parameter_dict is None or request_letter is None:
        raise HttpResponseBadRequest

    if not datarequest.middle_name or len(datarequest.middle_name.strip())<1:
        datarequest.middle_name = '_'

    ### Updating the other fields of the request
    datarequest.project_summary = parameter_dict['project_summary']
    datarequest.data_type_requested = parameter_dict['data_type_requested']

    if parameter_dict['purpose']  == 'other':
        datarequest.purpose = parameter_dict['purpose_other']
    else:
        datarequest.purpose = parameter_dict['purpose']

    datarequest.intended_use_of_dataset = parameter_dict['intended_use_of_dataset']

    if interest_layer:
        datarequest.jurisdiction_shapefile = interest_layer

    requester_name = unidecode(datarequest.first_name+" "+datarequest.last_name)
    letter = Document()
    letter_owner, created =  Profile.objects.get_or_create(username='dataRegistrationUploader')
    letter.owner = letter_owner
    letter.doc_file = request_letter
    letter.title = requester_name+ " Request Letter " +datetime.datetime.now().strftime("%Y-%m-%d")
    letter.is_published = False
    letter.save()
    letter.set_permissions( {"users":{"dataRegistrationUploader":["view_resourcebase"]}})

    datarequest.request_letter =letter;

    datarequest.save()

    return (datarequest, letter)

def map_letter_shapefile(datarequest=None, profile_session=None, interest_layer=None, request_letter = None):
    if interest_layer:
        datarequest.jurisdiction_shapefile = interest_layer

    requester_name = unidecode(profile_session.first_name+" "+profile_session.last_name)
    letter = Document()
    letter_owner, created =  Profile.objects.get_or_create(username='dataRegistrationUploader')
    letter.owner = letter_owner
    letter.doc_file = request_letter
    letter.title = requester_name+ " Request Letter " +datetime.datetime.now().strftime("%Y-%m-%d")
    letter.is_published = False
    letter.save()
    letter.set_permissions( {"users":{"dataRegistrationUploader":["view_resourcebase"]}})

    datarequest.request_letter =letter;

    # datarequest.save()

    return (datarequest, letter)
