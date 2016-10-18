from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView


from braces.views import (
    SuperuserRequiredMixin, LoginRequiredMixin,
)


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

class DataRequestList(LoginRequiredMixin, TemplateView):
    template_name = 'datarequests/data_request_list.html'
    raise_exception = True

def data_request_detail(request, pk, template='datarequests/profile_detail.html'):

    data_request = get_object_or_404(DataRequest, pk=pk)

    if not request.user.is_superuser and not data_request.profile == request.user:
        raise PermissionDenied

    context_dict={"data_request": data_request}
    
    if data_request.profile:
        context_dict['profile'] = data_request.profile
    if data_request.profile_request:
        context_dict['profile_request'] = data_request.profile_request
    
    if data_request.jurisdiction_shapefile:
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
    
    context_dict["request_reject_form"]= RejectionForm(instance=data_request)

    return render_to_response(template, RequestContext(request, context_dict))
