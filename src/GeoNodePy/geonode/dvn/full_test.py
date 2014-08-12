from __future__ import print_function

if __name__=='__main__':
    import os, sys
    DJANGO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(DJANGO_ROOT)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings.local'

import json

from style_layer_maker import StyleLayerMaker
from formatted_style_rules import FormattedStyleRules
from geonode_get_services import get_sld_rules


def run_test():
    
    # (1) We have the layer name
    layer_name = 'boston_census_r5j'
    
    #  http://localhost:8000/gs/rest/sldservice/geonode:boston_census_r5j/classify.xml?attribute=TWORACES&method=jenks&intervals=5&ramp=Custom&startColor=%23fff5f0&endColor=%2367000d&reverse=
    
    # (2) Make classficiation rules via geoserver's rest service
    d = dict(layer_name=layer_name\
                , attribute='TWORACES'\
                ,method='jenks'\
                ,intervals=5\
                ,ramp='Custom'\
                ,startColor='#fff5f0'\
                ,endColor='#67000d'\
                ,reverse=''\
            )
    resp_json = get_sld_rules(d)
    print(resp_json)
    resp_dict = json.loads(resp_json)
    if not resp_dict.get('success', False):
        print ('Failed to make rules')
        return

    sld_rule_data = resp_dict.get('data', {}).get('style_rules', None)
    if sld_rule_data is None:
        print ('Failed to find rules in response')
        
    # (3) Format rules into a full SLD
    sld_formatter = FormattedStyleRules(layer_name)
    formatted_rules_xml = sld_formatter.format_sld_xml(sld_rule_data)
    if formatted_rules_xml is None:
        print ('Failed to format xml')
        if sld_formatter.err_found:
            print ('\n'.join(sld_formatter.err_msgs))
        return
        
    print(formatted_rules_xml)
            
    # (4) Add new SLD to layer
    slm = StyleLayerMaker(layer_name)
    succcess = slm.add_sld_xml_to_layer(formatted_rules_xml)
    if succcess:
        print ('New layer added!')
    else:
        print ('Failed!')
        print ('\n'.join(slm.err_msgs))
    
if __name__=='__main__':
    run_test()