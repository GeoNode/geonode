#from bs4 import BeautifulSoup  # having issues with LXML case sensitivity on prettify

def update_sld_name(sld_str, new_sld_name):
    """
    Given an SLD (as a string), update the first two instances of <sld:Name>

    Note: The new_sld_name should be the Layer Name
    """
    if sld_str is None:
        return False, "The sld_str cannot be None"
    if new_sld_name is None:
        return False, "The new_sld_name cannot be None"

    start_tag = '<sld:Name>'
    end_tag = '</sld:Name>'

    # Look for 1st name tag
    start_idx = sld_str.find(start_tag)
    for loop in range(2):
        if start_idx == -1:
            break
        end_idx = sld_str.find(end_tag, start_idx+1)
        if start_idx == -1:
            break
        sld_str = '{0}{1}{2}'.format(\
                        sld_str[0:start_idx+len(start_tag)],
                        new_sld_name,
                        sld_str[end_idx:])
        # Look for next name tag
        start_idx = sld_str.find(start_tag, end_idx)

    print 'sld_str', sld_str

    return sld_str

    """
    soup = BeautifulSoup(sld_str, "lxml")

    for idx, sld_name in enumerate(soup.findAll('sld:name')):
        sld_name.string = new_sld_name
        if idx == 1:
            break

    return soup.prettify()
    """
"""
sld_str = '''<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0">
    <sld:NamedLayer>
        <sld:Name>boston_zip_codes_ek7b_m_0_u_g_p</sld:Name>
        <sld:UserStyle>
            <sld:Name>boston_zip_codes_ek7b_m_0_u_g_p</sld:Name>
            <sld:FeatureTypeStyle>
                <sld:Name>name</sld:Name>
                <sld:Rule>
                    <sld:PolygonSymbolizer>
                        <sld:Fill>
                            <sld:CssParameter name="fill">#880000</sld:CssParameter>
                        </sld:Fill>
                        <sld:Stroke>
                            <sld:CssParameter name="stroke">#ffbbbb</sld:CssParameter>
                            <sld:CssParameter name="stroke-width">0.7</sld:CssParameter>
                        </sld:Stroke>
                    </sld:PolygonSymbolizer>
                </sld:Rule>
            </sld:FeatureTypeStyle>
        </sld:UserStyle>
    </sld:NamedLayer>
</sld:StyledLayerDescriptor>'''
from bs4 import BeautifulSoup
soup = BeautifulSoup(sld_str, "lxml")
name_tag = soup.find('sld:Name')
"""
