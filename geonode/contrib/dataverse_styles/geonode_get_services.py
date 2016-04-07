"""
Convenience functions for making calls to the Geoserver Rest service


"""
if __name__ == '__main__':
    import os, sys
    DJANGO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(DJANGO_ROOT)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'

import urllib
try:
    from urlparse import urljoin
except:
    from urllib.parse import urljoin        # python 3.x
import xmltodict
import re
import logging

from django.conf import settings
from django.http import QueryDict

from geonode.maps.models import Layer
from geonode.contrib.dataverse_connect.dv_utils import remove_whitespace_from_xml, MessageHelperJSON
from geonode.contrib.dataverse_styles.sld_helper_form import SLDHelperForm

#from geonode.contrib.dataverse_styles.geoserver_rest_url_helper\
#    import get_retrieve_sld_rules_url, get_layer_features_definition_url

from geonode.contrib.dataverse_styles.geoserver_rest_util import make_geoserver_get_request
logger = logging.getLogger("geonode.contrib.dataverse_styles.geonode_get_services")

#WORLDMAP_WORKSPACE_NAME = settings.DEFAULT_WORKSPACE    #'geonode'


def get_retrieve_sld_rules_url(params_dict):
    """
    Format the URL used to retrieve SLD rules based on parameters

    Example: http://localhost:8080/geoserver/rest/sldservice/geonode:income_2so/classify.xml?reverse=&attribute=B19013_Med&ramp=Gray&endColor=%23A50F15&intervals=5&startColor=%23FEE5D9&method=equalInterval
    """
    if not type(params_dict) is dict:
        return None

    layer_name = params_dict.get('layer_name', None)
    if layer_name is None:
        return None

    params_dict.pop('layer_name')    # not needed for url query string
    encoded_params = urllib.urlencode(params_dict)

    sld_rules_fragment =  'rest/sldservice/%s:%s/classify.xml?%s' % (settings.DEFAULT_WORKSPACE, layer_name, encoded_params)

    sld_rules_url = urljoin(settings.GEOSERVER_BASE_URL, sld_rules_fragment)

    return sld_rules_url


def get_sld_rules(params):
    """
    Given the parameters defined in the SLDHelperForm:
        (1) Format the parameters as a GeoServer REST request
        (2) Make the request and retrieve the new XML rules

    :params dict: see the SLD HelperForm
    :returns: JSON message with data or error message

    Example of successful response:
    {"success": true, "data": {"style_rules": "<Rules><Rule><Title> &gt; -2.7786 AND &lt;= 2.4966</Title><Filter><And><PropertyIsGreaterThanOrEqualTo><PropertyName>Violence_4</PropertyName><Literal>-2.7786</Literal></PropertyIsGreaterThanOrEqualTo><PropertyIsLessThanOrEqualTo><PropertyName>Violence_4</PropertyName><Literal>2.4966</Literal></PropertyIsLessThanOrEqualTo></And></Filter><PolygonSymbolizer><Fill><CssParameter name=\"fill\">#424242</CssParameter></Fill><Stroke/></PolygonSymbolizer></Rule><Rule><Title> &gt; 2.4966 AND &lt;= 7.7718</Title><Filter><And><PropertyIsGreaterThan><PropertyName>Violence_4</PropertyName><Literal>2.4966</Literal></PropertyIsGreaterThan><PropertyIsLessThanOrEqualTo><PropertyName>Violence_4</PropertyName><Literal>7.7718</Literal></PropertyIsLessThanOrEqualTo></And></Filter><PolygonSymbolizer><Fill><CssParameter name=\"fill\">#676767</CssParameter></Fill><Stroke/></PolygonSymbolizer></Rule></Rules>"}}

    d = json.loads(json_response_str)
    xml_rules = d.get('data', {}).get('style_rules', None)

    Example of url sent to Geoserver:
    http://localhost:8080/geoserver/rest/sldservice/geonode:income_2so/classify.xml?reverse=&attribute=B19013_Med&ramp=Gray&endColor=%23A50F15&intervals=5&startColor=%23FEE5D9&method=equalInterval
    """
    #print('get_sld_rules.sld type: %s, params: %s' % (type(params), params))
    if not type(params) in (QueryDict, dict):
        return None

    # ----------------------------------
    # Make sure the params are valid
    # ----------------------------------
    f = SLDHelperForm(params)
    if not f.is_valid():
        #print ('form failed')
        return MessageHelperJSON.get_json_msg(success=False,\
            msg='The following errors were encounted:',\
            data_dict=f.get_error_list())

    # ----------------------------------
    # Create geoserver query url
    # ----------------------------------
    sld_rules_url = get_retrieve_sld_rules_url(f.get_url_params_dict())
    """
    print '-' *40
    print sld_rules_url
    print '-' *40
    """
    response, content = make_geoserver_get_request(sld_rules_url)
    #print 'response:', response

    # ----------------------------------
    # New rules not created -- possible bad data
    # ----------------------------------
    if content is not None and content == '<list/>':
        return MessageHelperJSON.get_json_msg(success=False,\
            msg='Error in creating style rules for layer. Bad parameters.')

    # ----------------------------------
    # Remove whitespace from XML
    # ----------------------------------
    content = remove_whitespace_from_xml(content)
    if content is None:
        return MessageHelperJSON.get_json_msg(success=False,\
            msg='Failed to remove whitespace from XML')

    # ----------------------------------
    # Were rules created?
    # ----------------------------------
    if not content.startswith('<Rules>'):
        return MessageHelperJSON.get_json_msg(success=False,\
            msg='Not able to create style rules for layer')

    # ----------------------------------
    # Wrap the XML rules in JSON and send them back
    # ----------------------------------
    return MessageHelperJSON.get_json_msg(success=True,\
        msg='', data_dict={ 'style_rules' : content })



def get_layer_features_definition_url(layer_name):
    """
    Example of url sent to Geoserver, where layer_name is "income_2so"
        http://localhost:8080/geoserver/rest/sldservice/geonode:income_2so/attributes.xml
    """
    if not layer_name:
        return None

    defn_url_fragment = 'rest/sldservice/%s:%s/attributes.xml' % (settings.DEFAULT_WORKSPACE, layer_name)
    defn_url = urljoin(settings.GEOSERVER_BASE_URL, defn_url_fragment)

    return defn_url


def get_layer_features_definition(layer_name):
    """Given a layer name, return the feature definition in JSON format

    :param layer_name: str
    :returns: JSON message with 'success' - true or false; and either 'message' or 'data'

    Example of successful JSON message:

    { "success": true", data": [{"name": "STATE", "type": "String"}, {"name": "Nbhd", "type": "String"}, {"name": "CT_ID_1", "type": "String"}, {"name": "UniqueID", "type": "Double"}, {"name": "NSA_ID_1", "type": "String"}, {"name": "B19013_Med", "type": "Double"}, {"name": "HOODS_PD_I", "type": "Double"}, {"name": "PERIMETER", "type": "Double"}, {"name": "COUNTY", "type": "String"}, {"name": "NSA_NAME", "type": "String"}, {"name": "Quality_of", "type": "Double"}, {"name": "DRY_PCT", "type": "Double"}, {"name": "DRY_ACRES", "type": "Double"}, {"name": "TRACT", "type": "String"}, {"name": "OBJECTID", "type": "Long"}, {"name": "BLK_COUNT", "type": "Integer"}, {"name": "AREA", "type": "Double"}, {"name": "NbhdCRM", "type": "String"}, {"name": "DRY_SQMI", "type": "Double"}, {"name": "the_geom", "type": "MultiPolygon"}, {"name": "SHAPE_LEN", "type": "Double"}, {"name": "LOGRECNO", "type": "String"}, {"name": "DRY_SQKM", "type": "Double"}, {"name": "UniqueID_1", "type": "Integer"}, {"name": "SHAPE_AREA", "type": "Double"}, {"name": "WALKABILIT", "type": "Double"}, {"name": "CT_ID", "type": "String"}, {"name": "Nbhd_1", "type": "String"}]}

    Example of failed JSON message:

    {"success": false, "message": "Definition not found for layer: \"income34x5\""}

    Example of url sent to Geoserver, where layer_name is "income_2so"
    http://localhost:8080/geoserver/rest/sldservice/geonode:income_2so/attributes.xml

    """
    if not layer_name:
        MessageHelperJSON.get_json_msg(success=False, msg="The layer name was not specified")

    # Does this layer exist
    if Layer.objects.filter(name=layer_name).count() == 0:
        MessageHelperJSON.get_json_msg(success=False, msg="The layer name, \"%s\" was not found in the system." % layer_name)

    # Create geoserver query url
    #query_url = 'rest/sldservice/geonode:%s/attributes.xml' % layer_name
    layer_defn_url =get_layer_features_definition_url(layer_name)
    #print (layer_defn_url)
    response, content = make_geoserver_get_request(layer_defn_url)


   # Layer definition not found!
    if content is not None and content == '<list/>':
        return MessageHelperJSON.get_json_msg(success=False, msg="Layer not found for name: \"%s\"" % layer_name)

    try:
        dict_content = xmltodict.parse(content)
    except:
        return MessageHelperJSON.get_json_msg(success=False, msg="Not able to convert field names for layer: \"%s\"" % layer_name)


    field_list = dict_content.get('Attributes', {}).get('Attribute', None)
    if field_list is None:
        return MessageHelperJSON.get_json_msg(success=False, msg="Field names not found for layer: \"%s\"" % layer_name)


    return MessageHelperJSON.get_json_msg(success=True, msg='', data_dict=field_list)


def get_sld_xml_for_layer(layer_name):
    """
    Given a layer name, return the SLD in XMl format

    Convenience method for calling WMS service on Geoserver:

    Example of url sent to Geoserver where layer name is "income_2so"

        http://localhost:8080/geoserver/wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetStyles&LAYERS=income_2so

    """
    if not layer_name:
        return (False, "The layer name was not specified")

    #--------------------------------
    # Does this layer exist?
    #--------------------------------
    if Layer.objects.filter(name=layer_name).count() == 0:
        return (False, \
            'The layer name "%s" was not found in the system.'\
            % layer_name)

    #--------------------------------
    # Create geoserver query url
    #   and make request
    #--------------------------------
    query_url = 'wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetStyles&LAYERS=%s' % (layer_name)
    get_styles_url = urljoin(settings.GEOSERVER_BASE_URL, query_url)

    response, sld_xml_content = make_geoserver_get_request(get_styles_url)

    if response:
        response_code = response.get('status', '(No status code set)')
        #print 'type(response_code)', type(response_code)
        if response_code != '200':
            err_msg = '''Call to Geoserver returned response code of %s when\
            trying to find layer "%s"''' % (response_code, layer_name)
            return (False, err_msg)

    if sld_xml_content is None:
        return (False, 'Failed to find SLD for layer: "%s"' % layer_name)

    return (True, sld_xml_content)


def get_style_name_for_layer(layer_name):
    """
    Retrieve a layer's existing file name by retrieving the SLD from
    Geoserver and parsing the XML
    """
    if layer_name is None:
        return (False, "The layer name was not specified")

    (success, sld_xml_or_err_msg) = get_sld_xml_for_layer(layer_name)

    #--------------------------------
    # An error was returned
    #--------------------------------
    if not success:
        return (False, sld_xml_or_err_msg)

    #--------------------------------
    # The style name is the 2nd value appearing
    # in the <sld:Name> tags
    #
    # In the example below, the style name is "social_disorder_shapefile_zip_kr33_d_n_e_b_v"
    #--------------------------------
    """
    <sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0">
    <sld:NamedLayer>
        <sld:Name>social_disorder_shapefile_zip_kr3</sld:Name>
        <sld:UserStyle>
            <sld:Name>social_disorder_shapefile_zip_kr33_d_n_e_b_v</sld:Name>
            <sld:IsDefault>1</sld:IsDefault>
    """
    l = re.findall('<sld:Name>(.*)</sld:Name>',\
                    sld_xml_or_err_msg,\
                    re.IGNORECASE)

    if l and len(l) >= 2:
        return (True, l[1])

    return (False, 'Failed to find the style name for layer: "%s"' % layer_name)



if __name__ == '__main__':
    test_layer_name = 'social_disorder_shapefile_zip_kr3'
    if 0:
        print get_layer_features_definition(test_layer_name)
        #http://localhost:8080/geoserver/rest/sldservice/geonode:boston_social_disorder_pbl/attributes.xml
        #http://localhost:8080/geoserver/gs/rest/sldservice/geonode:boston_social_disorder_pbl/classify.xml?reverse=&attribute=Violence_4&ramp=Gray&endColor=%23A50F15&intervals=5&startColor=%23FEE5D9&method=equalInterval

    if 1:
        get_sld_xml_for_layer(test_layer_name)

    if 1:
        d = dict(layer_name=test_layer_name\
                , attribute='Socdis_202'\
                , method='equalInterval'\
                , intervals=5\
                , ramp='Gray'\
                , startColor='#FEE5D9'\
                , endColor='#A50F15'\
                , reverse=''\
            )
        import json
        sld_rules = get_sld_rules(d)
        print sld_rules
        d2 = json.loads(sld_rules)
        print '-' * 80
        print d2.get('data', {}).get('style_rules', None)
        #print d2['data']['style_rules']#.keys()
