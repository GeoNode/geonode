import capra.layertypes.models as layertypes
from django.shortcuts import render_to_response
from django.template import RequestContext
from geonode.maps.views import browse_data
import json

def data(request):
    # typemap = dict([
    #     (link.layer.typename, str(link.category)) for link in layertypes.LayerTypeAssociation.objects.all()
    # ])
    # return render_to_response("data.html", RequestContext(request, {
    #     "typemap": json.dumps(typemap)
    # }))
    
    # use the standard view for now.
    return browse_data(request)