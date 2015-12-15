"""
12/15/2015 - THIS IS CURRENTLY OUTDATED....
"""
from __future__ import print_function

if __name__=='__main__':
    import os, sys
    DJANGO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(DJANGO_ROOT)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'#.local'

import json

from style_layer_maker import StyleLayerMaker
from style_rules_formatter import StyleRulesFormatter
from geonode_get_services import get_sld_rules


def run_test():

    # (1) We have the layer name
    layer_name = 'social_disorder_shapefile_zip_x7x'

    #  http://localhost:8000/gs/rest/sldservice/geonode:social_disorder_shapefile_zip_x7x/classify.xml?attribute=SocStrif_1&method=jenks&intervals=5&ramp=Custom&startColor=%23fff5f0&endColor=%2367000d&reverse=

    # (2) Make classficiation rules via geoserver's rest service
    d = dict(layer_name=layer_name\
                , attribute='SocStrif_1'\
                ,method='jenks'\
                ,intervals=5\
                ,ramp='Custom'\
                ,startColor='#fff5f0'\
                ,endColor='#67000d'\
                ,reverse=''\
            )
    resp_json = get_sld_rules(d)
    print ('-')
    print(resp_json)
    resp_dict = json.loads(resp_json)
    if not resp_dict.get('success', False):
        print ('Failed to make rules')
        return

    sld_rule_data = resp_dict.get('data', {}).get('style_rules', None)
    if sld_rule_data is None:
        print ('Failed to find rules in response')

    # (3) Format rules into a full SLD
    sld_formatter = StyleRulesFormatter(layer_name, '')
    if sld_formatter.format_sld_xml(sld_rule_data) is True:
        formatted_rules_xml = sld_formatter.formatted_sld_xml
    else:
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

def run_test2():
    xml_data = '''<sld:StyledLayerDescriptor xmlns:sld="http://www.opengis.net/sld" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd"><sld:NamedLayer><sld:Name>geonode:social_disorder_shapefile_zip_kr3</sld:Name><sld:UserStyle><sld:Name>social_disorder_shapefile_zip_kr3_v63sznt</sld:Name><sld:FeatureTypeStyle><sld:Rule><sld:Title> &gt; -3.3335 AND &lt;= 1.3938</sld:Title><ogc:Filter><ogc:And><ogc:PropertyIsGreaterThanOrEqualTo><ogc:PropertyName>SocStrif_1</ogc:PropertyName><ogc:Literal>-3.3335</ogc:Literal></ogc:PropertyIsGreaterThanOrEqualTo><ogc:PropertyIsLessThanOrEqualTo><ogc:PropertyName>SocStrif_1</ogc:PropertyName><ogc:Literal>1.3938</ogc:Literal></ogc:PropertyIsLessThanOrEqualTo></ogc:And></ogc:Filter><sld:PolygonSymbolizer><sld:Fill><sld:CssParameter name="fill">#000042</sld:CssParameter></sld:Fill><sld:Stroke/></sld:PolygonSymbolizer></sld:Rule><sld:Rule><sld:Title> &gt; 1.3938 AND &lt;= 6.121</sld:Title><ogc:Filter><ogc:And><ogc:PropertyIsGreaterThan><ogc:PropertyName>SocStrif_1</ogc:PropertyName><ogc:Literal>1.3938</ogc:Literal></ogc:PropertyIsGreaterThan><ogc:PropertyIsLessThanOrEqualTo><ogc:PropertyName>SocStrif_1</ogc:PropertyName><ogc:Literal>6.121</ogc:Literal></ogc:PropertyIsLessThanOrEqualTo></ogc:And></ogc:Filter><sld:PolygonSymbolizer><sld:Fill><sld:CssParameter name="fill">#000067</sld:CssParameter></sld:Fill><sld:Stroke/></sld:PolygonSymbolizer></sld:Rule><sld:Rule><sld:Title> &gt; 6.121 AND &lt;= 10.8481</sld:Title><ogc:Filter><ogc:And><ogc:PropertyIsGreaterThan><ogc:PropertyName>SocStrif_1</ogc:PropertyName><ogc:Literal>6.121</ogc:Literal></ogc:PropertyIsGreaterThan><ogc:PropertyIsLessThanOrEqualTo><ogc:PropertyName>SocStrif_1</ogc:PropertyName><ogc:Literal>10.8481</ogc:Literal></ogc:PropertyIsLessThanOrEqualTo></ogc:And></ogc:Filter><sld:PolygonSymbolizer><sld:Fill><sld:CssParameter name="fill">#00008B</sld:CssParameter></sld:Fill><sld:Stroke/></sld:PolygonSymbolizer></sld:Rule><sld:Rule><sld:Title> &gt; 10.8481 AND &lt;= 15.5753</sld:Title><ogc:Filter><ogc:And><ogc:PropertyIsGreaterThan><ogc:PropertyName>SocStrif_1</ogc:PropertyName><ogc:Literal>10.8481</ogc:Literal></ogc:PropertyIsGreaterThan><ogc:PropertyIsLessThanOrEqualTo><ogc:PropertyName>SocStrif_1</ogc:PropertyName><ogc:Literal>15.5753</ogc:Literal></ogc:PropertyIsLessThanOrEqualTo></ogc:And></ogc:Filter><sld:PolygonSymbolizer><sld:Fill><sld:CssParameter name="fill">#0000B0</sld:CssParameter></sld:Fill><sld:Stroke/></sld:PolygonSymbolizer></sld:Rule><sld:Rule><sld:Title> &gt; 15.5753 AND &lt;= 20.302599999999998</sld:Title><ogc:Filter><ogc:And><ogc:PropertyIsGreaterThan><ogc:PropertyName>SocStrif_1</ogc:PropertyName><ogc:Literal>15.5753</ogc:Literal></ogc:PropertyIsGreaterThan><ogc:PropertyIsLessThanOrEqualTo><ogc:PropertyName>SocStrif_1</ogc:PropertyName><ogc:Literal>20.302599999999998</ogc:Literal></ogc:PropertyIsLessThanOrEqualTo></ogc:And></ogc:Filter><sld:PolygonSymbolizer><sld:Fill><sld:CssParameter name="fill">#0000D4</sld:CssParameter></sld:Fill><sld:Stroke/></sld:PolygonSymbolizer></sld:Rule></sld:FeatureTypeStyle></sld:UserStyle></sld:NamedLayer></sld:StyledLayerDescriptor>'''

    geonode_url = 'http://localhost:8080/geoserver/rest/styles/social_disorder_shapefile_zip_kr3.xml'

    content_type = 'application/vnd.ogc.sld+xml; charset=UTF-8'
    headers["Content-Type"] = content_type

    r = requests.put(geonode_url,\
            data=xml_data,\
            headers=headers
                )
    print r.status_code
    print r.text

if __name__=='__main__':
    run_test2()
    #run_test()
