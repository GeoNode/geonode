from __future__ import print_function

import json
import logging
import sys

from django.conf import settings

from geonode.dvn.dv_utils import MessageHelperJSON
from geonode.dvn.sld_helper_form import SLDHelperForm
from geonode.dvn.style_layer_maker import StyleLayerMaker
from geonode.dvn.formatted_style_rules import FormattedStyleRules
from geonode.dvn.geonode_get_services import get_sld_rules

logger = logging.getLogger("geonode.dvn.layer_styler")

class LayerStyler:
    def __init__(self, styling_params):
        self.styling_params = styling_params
        self.layer_name = None
        self.err_found = False
        self.err_msgs = []
        self.layer_metadata = None
    
    
    def add_err_msg(self, msg):
        self.err_found = True
        self.err_msgs.append(msg)
        logger.warn(msg)

  
    def get_json_as_dict(self, resp_json, default_msg):
        try:
            return json.loads(resp_json)
        except:
            return {'success' : False, 'message' : default_msg}
    
    
    def style_layer(self):
        
        # (1) Check params and create rules
        #
        sld_rule_data = self.set_layer_name_and_get_rule_data()
        if sld_rule_data is None:
            return False
        
        # (2) Format rules into full SLD
        #
        formatted_sld_object = self.format_rules_into_full_sld(sld_rule_data)
        if formatted_sld_object is None:
            return False
        
        # (3) Add new SLD to Layer
        #
        return self.add_new_sld_to_layer(formatted_sld_object)
    

    def set_layer_name_and_get_rule_data(self):
        """
        (1) Check params and create rules
        """
        if self.styling_params is None:
            return None
        resp_json = get_sld_rules(self.styling_params)
        resp_dict = self.get_json_as_dict(resp_json, 'Failed to make the SLD rules')
        
        if not resp_dict.get('success') is True:
            msg = resp_dict.get('message',)
            self.add_err_msg(msg)
            for err_msg in resp_dict.get('data', []):
                self.add_err_msg(err_msg)
            return None

        # (1a) Pull layer name from initial params, should never fail b/c params have been evaluated in (1)
        #
        self.layer_name = self.styling_params.get('layer_name', None)
        if self.layer_name is None:
            self.add_err_msg('Layer name is not in the parameters')
            return None

        sld_rule_data = resp_dict.get('data', {}).get('style_rules', None)
        if sld_rule_data is None:
            self.add_err_msg('Failed to find rules in response')
            return None
        
        return sld_rule_data
        

    def format_rules_into_full_sld(self, sld_rule_data):
        """ 
        (2) Format rules into full SLD
        """
        if not sld_rule_data:
            self.add_err_msg('Rule data is not available')
            return None

        if not self.layer_name:
            self.add_err_msg('Layer name is not available')
            return None

        sld_formatter = FormattedStyleRules(self.layer_name)

        sld_formatter.format_sld_xml(sld_rule_data)

        if sld_formatter.err_found:
            self.add_err_msg('Failed to format xml')
            if sld_formatter.err_found:
                self.add_err_msg('\n'.join(formatted_sld.err_msgs))
            return None

        return sld_formatter
        
    
    def add_new_sld_to_layer(self, formatted_sld_object):
        """ 
        (3) Add new SLD to Layer
        """
        if not formatted_sld_object:
            self.add_err_msg('Formatted SLD data is not available')
            return False
        
        slm = StyleLayerMaker(self.layer_name)
        success = slm.add_sld_to_layer(formatted_sld_object)
        if success:
            self.layer_metadata = slm.layer_metadata
            return True
    
        for err in slm.err_msgs:
            self.add_err_msg(err)
        
        return False
        

    def get_json_message(self):

        if self.layer_metadata is not None:
            metadata_dict = self.layer_metadata.get_metadata_dict()
            if metadata_dict:
                return MessageHelperJSON.get_json_msg(success=True, msg='', data_dict=metadata_dict)
            else:
                logger.error('LayerStyler. Failed to retrieve metadata dict for layer [%s]' % (self.layer_name))
                return MessageHelperJSON.get_json_msg(success=False, msg='Fail to create metadata dict')

        err_msg = '\n'.join(self.err_msgs)
        if not err_msg:
            err_msg = 'Failed to create layer.  Please try again'

        return MessageHelperJSON.get_json_msg(success=False, msg=err_msg)
        

if __name__=='__main__':
    from geonode_get_services import get_layer_features_definition
    layer_name = 'income_bfe'
    #print (get_layer_features_definition(layer_name))
    
    d = dict(layer_name=layer_name\
                , attribute='B19013_Med'\
                ,method='quantile'\
                ,intervals=2\
                ,ramp='Random'\
                ,startColor='#fff5f0'\
                ,endColor='#67000d'\
                ,reverse=''\
            )
    ls = LayerStyler(d)
    worked = ls.style_layer()
    if not worked:
        print ('\n'.join(ls.err_msgs))
    #else:
    #    print ('Yes!')
    #    metadata = ls.layer_metadata
    #    if metadata:
    #        print (metadata.get_metadata_dict())
    print ('-'*40)       
    print (ls.get_json_message())