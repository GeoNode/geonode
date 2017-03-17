from django.utils import timezone
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import (
    redirect, get_object_or_404, render, render_to_response)
from django.template import RequestContext
from django.utils import simplejson as json
from django.views.generic import TemplateView

from braces.views import (
    SuperuserRequiredMixin, LoginRequiredMixin,
)

from urlparse import parse_qs

from geonode.cephgeo.models import TileDataClass
from geonode.cephgeo.models import UserJurisdiction
from geonode.datarequests.admin_edit_forms import DataRequestEditForm
from geonode.datarequests.forms import DataRequestRejectForm
from geonode.datarequests.models import DataRequest
from geonode.documents.models import get_related_documents
from geonode.security.views import _perms_info_json
from geonode.tasks.jurisdiction import place_name_update
from geonode.tasks.jurisdiction2 import compute_size_update, assign_grid_refs_all, assign_grid_refs
from geonode.utils import default_map_config, resolve_object, llbbox_to_mercator
from geonode.utils import GXPLayer, GXPMap

from pprint import pprint

import csv

@login_required
def data_requests_csv(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')

    response = HttpResponse(content_type='text/csv')
    datetoday = timezone.now()
    response['Content-Disposition'] = 'attachment; filename="datarequests-"'+str(datetoday.month)+str(datetoday.day)+str(datetoday.year)+'.csv"'

    writer = csv.writer(response)
    fields = ['id','name','email','contact_number', 'organization', 'org_type','has_profile_request','has_letter','has_shapefile','project_summary', 'created','status', 'status_changed','rejection_reason','juris_data_size','area_coverage']
    writer.writerow( fields)

    objects = DataRequest.objects.all().order_by('pk')

    for o in objects:
        writer.writerow(o.to_values_list(fields))

    return response

class DataRequestList(LoginRequiredMixin, TemplateView):
    template_name = 'datarequests/data_request_list.html'
    raise_exception = True

@login_required
def user_data_request_list(request):
    data_requests = DataRequest.objects.filter(profile=request.user)

    return None

def data_request_detail(request, pk, template='datarequests/data_detail.html'):

    data_request = get_object_or_404(DataRequest, pk=pk)

    if not request.user.is_superuser and not data_request.profile == request.user:
        return HttpResponseRedirect('/forbidden')

    context_dict={"data_request": data_request}
    context_dict ['data_types'] = data_request.data_type.names()
    pprint(context_dict ['data_types'])
    pprint("dr.pk="+str(data_request.pk))

    if data_request.profile:
        context_dict['profile'] = data_request.profile

    if data_request.profile_request:
        context_dict['profile_request'] = data_request.profile_request

    if data_request.jurisdiction_shapefile:
         layer = data_request.jurisdiction_shapefile
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

    context_dict["request_reject_form"]= DataRequestRejectForm(instance=data_request)

    return render_to_response(template, RequestContext(request, context_dict))
    
@login_required
def data_request_edit(request, pk, template ='datarequests/data_detail_edit.html'):
    data_request = get_object_or_404(DataRequest, pk=pk)
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')
    
    if request.method == 'GET': 
        context_dict={"data_request":data_request}
        initial_data = model_to_dict(data_request)
        if not DataRequestEditForm.INTENDED_USE_CHOICES.__contains__(initial_data['purpose']):
            initial_data['purpose_other'] = initial_data['purpose'] 
            initial_data['purpose'] = 'other'
            
        context_dict["form"] = DataRequestEditForm(initial = initial_data)
        return render(request, template, context_dict)
    else:
        form = DataRequestEditForm(request.POST)
        if form.is_valid():
            pprint("form is valid")
            for k, v in form.cleaned_data.iteritems():
                if k == 'data_class_requested':
                    data_types = []
                    data_request.data_type.clear()
                    for i in v:
                        data_request.data_type.add(str(i.short_name))
                    #remove original tags
                elif k=='purpose':
                    if v == form.INTENDED_USE_CHOICES.other:
                        setattr(data_request,k,form.cleaned_data.get('purpose_other'))
                    else:
                        setattr(data_request,k,v)
                else:
                    setattr(data_request, k, v)
            data_request.administrator = request.user
            data_request.save()
        else:
            pprint("form is invalid")
            pprint(form.errors)
            return render( request, template, {'form': form, 'data_request': data_request})
        return HttpResponseRedirect(data_request.get_absolute_url())

def data_request_cancel(request, pk):
    data_request = get_object_or_404(DataRequest, pk=pk)
    if not request.user.is_superuser and not data_request.profile == request.user:
        return HttpResponseRedirect('/forbidden')

    if not request.method == 'POST':
        pprint("user is not an HTTP POST")
        return HttpResponseRedirect('/forbidden')

    if data_request.status == 'pending':
        form = parse_qs(request.POST.get('form', None))
        data_request.rejection_reason = form['rejection_reason'][0]
        data_request.save()

        if not request.user.is_superuser:
            data_request.set_status('cancelled')
        else:
            data_request.set_status('cancelled',administrator = request.user)

    url = request.build_absolute_uri(data_request.get_absolute_url())

    return HttpResponse(
        json.dumps({
            'result': 'success',
            'errors': '',
            'url': url}),
        status=200,
        mimetype='text/plain'
    )

def data_request_approve(request, pk):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')
    if not request.method == 'POST':
        return HttpResponseRedirect('/forbidden')

    if request.method == 'POST':
        data_request = get_object_or_404(DataRequest, pk=pk)

        if not data_request.profile:
            if data_request.profile_request:
                if not data_request.profile_request.status == 'approved':
                    messages.info(request, "Data request #"+str(pk)+" cannot be approved because the requester does not have an approved user yet.")
                    return HttpResponseRedirect(data_request.get_absolute_url())
                    #return HttpResponseRedirect('/forbidden')
                else:
                    data_request.profile = profile_request.profile
                    data_request.save()

        if data_request.jurisdiction_shapefile:
            data_request.assign_jurisdiction() #assigns/creates jurisdiction object
            assign_grid_refs.delay(data_request.profile)
        else:
            try:
                uj = UserJurisdiction.objects.get(user=data_request.profile)
                uj.delete()
            except ObjectDoesNotExist as e:
                pprint("Jurisdiction Shapefile not found, nothing to delete. Carry on")


        data_request.set_status('approved',administrator = request.user)
        data_request.send_approval_email(data_request.profile.username)
        messages.info(request, "Request "+str(pk)+" has been approved.")

        return HttpResponseRedirect(data_request.get_absolute_url())

    else:
        return HttpResponseRedirect("/forbidden/")

def data_request_reject(request, pk):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden/')

    if not request.method == 'POST':
         return HttpResponseRedirect('/forbidden/')

    data_request = get_object_or_404(DataRequest, pk=pk)

    if data_request.status == 'pending':
        form = parse_qs(request.POST.get('form', None))
        data_request.rejection_reason = form['rejection_reason'][0]
        if 'additional_rejection_reason' in form.keys():
            data_request.additional_rejection_reason = form['additional_rejection_reason'][0]
        data_request.save()

        data_request.set_status('rejected',administrator = request.user)
        data_request.send_rejection_email()

    url = request.build_absolute_uri(data_request.get_absolute_url())

    return HttpResponse(
        json.dumps({
            'result': 'success',
            'errors': '',
            'url': url}),
        status=200,
        mimetype='text/plain'
    )

def data_request_compute_size_all(request):
    if request.user.is_superuser:
        data_requests = DataRequest.objects.exclude(jurisdiction_shapefile=None)
        compute_size_update.delay(data_requests)
        messages.info(request, "The estimated data size area coverage of the requests are currently being computed")
        return HttpResponseRedirect(reverse('datarequests:data_request_browse'))
    else:
        return HttpResponseRedirect('/forbidden')


def data_request_compute_size(request, pk):
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

def data_request_reverse_geocode_all(request):
    if request.user.is_superuser:
        data_requests = DataRequest.objects.exclude(jurisdiction_shapefile=None)
        place_name_update.delay(data_requests)
        messages.info(request,"Retrieving approximated place names of data requests")
        return HttpResponseRedirect(reverse('datarequests:data_request_browse'))
    else:
        return HttpResponseRedirect('/forbidden/')

def data_request_reverse_geocode(request, pk):
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
    #if not request.user.is_superuser:
    #    return HttpResponseRedirect('/forbidden')

    if not request.method == 'POST':
        return HttpResponseRedirect('/forbidden')

    facets_count = {}

    if not request.user.is_superuser:
        facets_count = {
            'pending': DataRequest.objects.filter(
                status='pending', profile=request.user).count(),
            'approved': DataRequest.objects.filter(
                status='approved', profile=request.user).count(),
            'rejected': DataRequest.objects.filter(
                status='rejected', profile=request.user).count(),
            'cancelled': DataRequest.objects.filter(
                status='cancelled', profile=request.user).count(),
        }
    else:
        facets_count = {
            'pending': DataRequest.objects.filter(
                status='pending').count(),
            'approved': DataRequest.objects.filter(
                status='approved').count(),
            'rejected': DataRequest.objects.filter(
                status='rejected').count(),
            'cancelled': DataRequest.objects.filter(
                status='cancelled').count(),
        }

    return HttpResponse(
        json.dumps(facets_count),
        status=200,
        mimetype='text/plain'
    )
