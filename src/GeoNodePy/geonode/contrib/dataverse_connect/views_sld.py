import json
import urllib
import logging

from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from shared_dataverse_information.layer_classification.forms_api import ClassifyRequestDataForm, LayerAttributeRequestForm
from geonode.contrib.dataverse_layer_metadata.forms import CheckForExistingLayerFormWorldmap
from shared_dataverse_information.shared_form_util.format_form_errors import format_errors_as_text

from geonode.contrib.dataverse_connect.layer_metadata import LayerMetadata
from geonode.contrib.dataverse_connect.dv_utils import MessageHelperJSON
from geonode.contrib.dataverse_connect.geonode_get_services import get_layer_features_definition
from geonode.contrib.dataverse_connect.sld_helper_form import SLDHelperForm
from geonode.contrib.dataverse_connect.layer_styler import LayerStyler
from geonode.contrib.dataverse_connect.layer_metadata import LayerMetadata


logger = logging.getLogger("geonode.contrib.dataverse_connect.views_sld")

#from proxy.views import geoserver_rest_proxy

# http://localhost:8000/gs/rest/sldservice/geonode:boston_social_disorder_pbl/classify.xml?attribute=Violence_4&method=equalInterval&intervals=5&ramp=Gray&startColor=%23FEE5D9&endColor=%23A50F15&reverse=



@csrf_exempt
def view_layer_classification_attributes(request):
    """
    Given a layer name, return attributes for that layer to be used in the GeoConnect classification form.
    """    
    # Auth check embedded in params, handled by LayerAttributeRequestForm
    
    if not request.POST:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="use a POST request")    
        return HttpResponse(status=405, content=json_msg, content_type="application/json")

    api_form = LayerAttributeRequestForm(request.POST.dict())
    if not api_form.is_valid():
        #
        #   Invalid, send back an error message
        #
        logger.error("Classfication error import error: \n%s" % format_errors_as_text(api_form))
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                                , msg="Incorrect params for LayerAttributeRequestForm: <br />%s" % api_form.errors)
        return HttpResponse(status=400, content=json_msg, content_type="application/json")
    
    if not api_form.is_signature_valid_check_post(request):
        #
        #   Invalid signature on request
        #
        logger.error("Invalid signature on request.  Failed validation with LayerAttributeRequestForm")
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                                , msg="Invalid signature on request.  Failed validation with LayerAttributeRequestForm")
        return HttpResponse(status=400, content=json_msg, content_type="application/json")
    
    #-------------
    # Make sure this is a WorldMap layer that we're classifying
    #-------------
    f = CheckForExistingLayerFormWorldmap(request.POST)
    if not f.is_valid():    # This should always pass....
        logger.error("Unexpected form validation error in CheckForExistingLayerFormWorldmap. Errors: %s" % f.errors)
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                            , msg="Invalid data for classifying an existing layer.")
        return HttpResponse(status=400, content=json_msg, content_type="application/json")

    if not f.legitimate_layer_exists(request.POST):
        err_msg = "The layer to classify could not be found.  This may not be a Dataverse-created layer."
        logger.error(err_msg)
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                            , msg=err_msg)
        return HttpResponse(status=400, content=json_msg, content_type="application/json")


    json_msg = get_layer_features_definition(api_form.cleaned_data.get('layer_name', ''))
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
    
    # Auth check embedded in params, handled by ClassifyRequestDataForm

    if not request.POST:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="use a POST request")    
        return HttpResponse(status=405, content=json_msg, content_type="application/json")

    
    Post_Data_As_Dict = request.POST.dict()
    api_form = ClassifyRequestDataForm(Post_Data_As_Dict)
    if not api_form.is_valid():
        #
        #   Invalid, send back an error message
        #
        logger.error("Classfication error import error: \n%s" % format_errors_as_text(api_form))
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                                , msg="Incorrect params for ClassifyRequestDataForm: <br />%s" % api_form.errors)

        return HttpResponse(status=400, content=json_msg, content_type="application/json")
        

    if not api_form.is_signature_valid_check_post(request):
        #
        #   Invalid signature on request
        #
        logger.error("Invalid signature on request.  Failed validation with ClassifyRequestDataForm")
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                                , msg="Invalid signature on request.  Failed validation with ClassifyRequestDataForm")
        return HttpResponse(status=400, content=json_msg, content_type="application/json")
    

    #-------------
    # Make sure this is a WorldMap layer that we're classifying
    #-------------
    f = CheckForExistingLayerFormWorldmap(request.POST)
    if not f.is_valid():    # This should always pass....
        logger.error("Unexpected form validation error in CheckForExistingLayerFormWorldmap. Errors: %s" % f.errors)
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                            , msg="Invalid data for classifying an existing layer.")
        return HttpResponse(status=400, content=json_msg, content_type="application/json")
    
    if not f.legitimate_layer_exists(request.POST):
        err_msg = "The layer to classify could not be found.  This may not be a Dataverse-created layer."
        logger.error(err_msg)
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                            , msg=err_msg)
        return HttpResponse(status=400, content=json_msg, content_type="application/json")
        
    
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

