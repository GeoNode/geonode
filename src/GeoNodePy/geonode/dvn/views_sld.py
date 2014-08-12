import json
import urllib

from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from geonode.dvn.layer_metadata import LayerMetadata

from geonode.dvn.dv_utils import MessageHelperJSON
from geonode.dvn.dataverse_auth import has_proper_auth
from geonode.dvn.geonode_get_services import get_layer_features_definition
from geonode.dvn.sld_helper_form import SLDHelperForm
from geonode.dvn.layer_styler import LayerStyler
from geonode.dvn.layer_metadata import LayerMetadata

#from proxy.views import geoserver_rest_proxy

# http://localhost:8000/gs/rest/sldservice/geonode:boston_social_disorder_pbl/classify.xml?attribute=Violence_4&method=equalInterval&intervals=5&ramp=Gray&startColor=%23FEE5D9&endColor=%23A50F15&reverse=

@csrf_exempt
def view_layer_feature_defn(request, layer_name):
    """
    Given a layer name, retrieve a desciption of the field names in values.
    This will be in XML format.
    
    example: http://localhost:8000/dvn/describe-features/income_4x5/
    """    
    if not has_proper_auth(request):
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Authentication failed.")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")
        
    json_msg = get_layer_features_definition(layer_name)
    return HttpResponse(content=json_msg, content_type="application/json")


@csrf_exempt
def view_layer_classify_params(request, layer_name):
    """
    Given a layer name, return attributes needed to run a GeoConnect classification form.
    
    This includes:
        - attributes
        - formulas
        - colors
    on Geo a desciption of the field names in values.
    This will be in XML format.

    example: http://localhost:8000/dvn/describe-features/income_4x5/
    """    
    if not has_proper_auth(request):
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Authentication failed.")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")
    
    json_msg = get_layer_features_definition(layer_name)
    return HttpResponse(content=json_msg, content_type="application/json")
            
    

@csrf_exempt
def view_create_new_layer_style(request):
    """
    Send in a POST request with parameters that conform to the attributes in the sld_helper_form.SLDHelperForm
    
    Encapsulates 3 steps: 
        (1) Based on parameters, create new classfication rules and embed in SLD XML
        (2) Make the classification rules the default style for the given layer
        (3) Return links to the newly styled layer -- or an error message
    
    :returns: JSON message with either an error or data containing links to the update classification layer
    
    """
    if not has_proper_auth(request):
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Authentication failed.")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")

    if not request.POST:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="use a POST request")    
        return HttpResponse(status=405, content=json_msg, content_type="application/json")

    ls = LayerStyler(request.POST)
    ls.style_layer()

    print 'post style'
    if ls.err_found:
        print 'has an error!'
        print '\n'.join(ls.err_msgs)
    else:
        print 'not bad'

    json_msg = ls.get_json_message()    # Will determine success/failure and appropriate params
    
    return HttpResponse(content=json_msg, content_type="application/json")

