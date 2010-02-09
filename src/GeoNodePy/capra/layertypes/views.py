import capra.layertypes.models as layertypes
from django.shortcuts import render_to_response
from django.conf import settings
import json

def data(request):
    typemap = dict([
        (link.layer.typename, str(link.category)) for link in layertypes.LayerTypeAssociation.objects.all()
    ])
    return render_to_response("data.html", {
        "typemap": json.dumps(typemap),
        "GEOSERVER_BASE_URL": settings.GEOSERVER_BASE_URL
    })
