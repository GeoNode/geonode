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
