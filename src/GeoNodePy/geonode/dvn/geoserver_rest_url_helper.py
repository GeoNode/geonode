

from django.conf import settings
import urllib
try:
    from urlparse import urljoin
except:
    from urllib.parse import urljoin        # python 3.x
    
    
from geonode.dvn.sld_helper_form import SLDHelperForm


WORLDMAP_WORKSPACE_NAME = 'geonode'
    
def get_retrieve_sld_rules_url(params_dict):
    """
    URL used to retrieve SLD rules based on parameters

    Example: http://localhost:8080/geoserver/rest/sldservice/geonode:income_2so/classify.xml?reverse=&attribute=B19013_Med&ramp=Gray&endColor=%23A50F15&intervals=5&startColor=%23FEE5D9&method=equalInterval
    
    """
    if not type(params_dict) is dict:
        return None
        
    layer_name = params_dict.get('layer_name', None)
    if not layer_name:
        return None
    
    params_dict.pop('layer_name')    # not needed for url query string
    
    encoded_params = urllib.urlencode(params_dict)
    sld_rules_fragment =  'rest/sldservice/%s:%s/classify.xml?%s' % (WORLDMAP_WORKSPACE_NAME, layer_name, encoded_params)
    sld_rules_url = urljoin(settings.GEOSERVER_BASE_URL, sld_rules_fragment)
    
    return sld_rules_url


def get_layer_features_definition_url(layer_name):
    """
    Example of url sent to Geoserver, where layer_name is "income_2so"
        http://localhost:8080/geoserver/rest/sldservice/geonode:income_2so/attributes.xml
    """
    if not layer_name:
        return None

    defn_url_fragment = 'rest/sldservice/%s:%s/attributes.xml' % (WORLDMAP_WORKSPACE_NAME, layer_name)
    defn_url = urljoin(settings.GEOSERVER_BASE_URL, defn_url_fragment)

    return defn_url
    
    
def get_set_sld_rules_to_layer_url(layer_name):
    """
     Create url to set the new SLD to the layer via a put
     #http://localhost:8000/gs/rest/styles/social_disorder_nydj_k_i_v.xml
    
        This will be sent with a XML content containing the SLD rules
    """
    if not layer_name:
        return None
    
    url_fragment = 'rest/styles/%s.xml' % (layer_name)
    full_url = urljoin(settings.GEOSERVER_BASE_URL, url_fragment)

    return full_url
    


def get_set_default_style_url(layer_name):
    
    if not layer_name:
        return None
        
    url_fragment = 'rest/layers/%s:%s' % (WORLDMAP_WORKSPACE_NAME, layer_name)
    full_url = urljoin(settings.GEOSERVER_BASE_URL, url_fragment)

    return full_url
    
    #geoserver_json_url = urljoin(settings.GEOSERVER_BASE_URL, 'rest/layers/geonode:%s' % (layer_name))
    
    
    