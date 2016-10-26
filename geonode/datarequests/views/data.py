from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    redirect, get_object_or_404, render, render_to_response)
from django.views.generic import TemplateView

from braces.views import (
    SuperuserRequiredMixin, LoginRequiredMixin,
)

from urlparse import parse_qs

from geonode.datarequests.forms import DataRequestRejectForm
from geonode.datarequests.models import DataRequest

@login_required
def data_request_csv(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')

    response = HttpResponse(content_type='text/csv')
    datetoday = timezone.now()
    response['Content-Disposition'] = 'attachment; filename="datarequests-"'+str(datetoday.month)+str(datetoday.day)+str(datetoday.year)+'.csv"'

    writer = csv.writer(response)
    fields = ['id','name','email','contact_number', 'organization', 'organization_type','organization_other','has_letter','has_shapefile','project_summary', 'created','status', 'status changed','rejection_reason','juris_data_size','area_coverage']
    writer.writerow( fields)

    objects = DataRequest.objects.all().order_by('pk')

    for o in objects:
        writer.writerow(o.to_values_list(fields))

    return response

class DataRequestList(LoginRequiredMixin, TemplateView):
    template_name = 'datarequests/data_request_list.html'
    raise_exception = True

def data_request_detail(request, pk, template='datarequests/profile_detail.html'):

    data_request = get_object_or_404(DataRequest, pk=pk)

    if not request.user.is_superuser and not data_request.profile == request.user:
        return HttpResponseRedirect('/forbidden')

    context_dict={"data_request": data_request}
    
    if data_request.profile:
        context_dict['profile'] = data_request.profile
    elif data_request.profile_request:
        context_dict['profile'] = data_request.profile_request
    
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
    
         if settings.SOCIAL_ORIGINS:
             context_dict["social_links"] = build_social_links(request, layer)
    
    context_dict["request_reject_form"]= DataRequestRejectForm(instance=data_request)

    return render_to_response(template, RequestContext(request, context_dict))

def data_request_cancel(request, pk):
    data_request = get_object_or_404(DataRequest, pk=pk)
    if not request.user.is_superuser or not data_request.profile == request.user:
        return HttpResponseRedirect('/forbidden')

    if not request.method == 'POST':
        return HttpResponseRedirect('/forbidden')

    if data_request.request_status == 'pending':
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
        
        if not data_request.status == 'pending':
            return HttpResponseRedirect('/forbidden')
        
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
        data_request.send_approval_email()
        messages.info("Request "+str(pk)+" has been approved.")
        
        return HttpResponseRedirect(data_request.get_absolute_url())

    else:
        return HttpResponseRedirect("/forbidden/")

def data_request_reject(request, pk):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden/')

    if not request.method == 'POST':
         return HttpResponseRedirect('/forbidden/')

    data_request = get_object_or_404(DataRequest, pk=pk)

    if data_request.request_status == 'pending':
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

def data_request_compute_size(request):
    if request.user.is_superuser:
        data_requests = DataRequest.objects.exclude(jurisdiction_shapefile=None)
        compute_size_update.delay(data_requests)
        messages.info(request, "The estimated data size area coverage of the requests are currently being computed")
        return HttpResponseRedirect(reverse('datarequests:data_request_browse'))
    else:
        return HttpResponseRedirect('/forbidden/')


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

def data_request_reverse_geocode(request):
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
                status='pending', profile=request.user).exclude(date=None).count(),
            'approved': DataRequest.objects.filter(
                status='approved', profile=request.user).count(),
            'rejected': DataRequest.objects.filter(
                status='rejected', profile=request.user).count(),
            'cancelled': DataRequest.objects.filter(
                status='cancelled', profile=request.user).exclude(date=None).count(),
        }
    else:
        facets_count = {
            'pending': DataRequest.objects.filter(
                status='pending').exclude(date=None).count(),
            'approved': DataRequest.objects.filter(
                status='approved').count(),
            'rejected': DataRequest.objects.filter(
                status='rejected').count(),
            'cancelled': DataRequest.objects.filter(
                status='cancelled').exclude(date=None).count(),
        }

    return HttpResponse(
        json.dumps(facets_count),
        status=200,
        mimetype='text/plain'
    )
