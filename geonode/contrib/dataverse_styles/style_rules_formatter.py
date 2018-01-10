"""
Basic string formatting to take a new set of style rules
and create a layer specific SLD in XML format
"""
from __future__ import print_function

if __name__=='__main__':
    import os, sys
    DJANGO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(DJANGO_ROOT)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings.local'

from django.conf import settings
import logging
import random
import string
import re
from lxml import etree

from geonode.contrib.dataverse_connect.dv_utils import remove_whitespace_from_xml, MessageHelperJSON
from geonode.contrib.msg_util import dashes, msg, msgt


LOGGER = logging.getLogger(__name__)

class StyleRulesFormatter(object):
    """
    Usage.  Create a new SLD used for re-styling a layer
    """

    RULES_START_TAG = '<Rules>'
    RULES_END_TAG = '</Rules>'

    def __init__(self, layer_name, **kwargs):
        self.layer_name = layer_name
        self.sld_name = kwargs.get('sld_name', None)

        self.is_point_layer = kwargs.get('is_point_layer', False)
        self.current_sld = kwargs.get('current_sld', None)

        # Randomly generated extension to the layer name
        #   - Ability to add an set id, used for tests
        self.predefined_id = kwargs.get('predefined_id', None)

        self.formatted_sld_xml = None
        self.err_found = False
        self.err_msgs = []

        if self.sld_name is None:
            self.sld_name = self.generate_sld_name()

    def add_err_msg(self, err_msg):
        self.err_found = True
        self.err_msgs.append(err_msg)
        LOGGER.warn(err_msg)

    def id_generator(self, size=7, chars=string.ascii_lowercase + string.digits):
        """
        Create a random id used to generate an SLD name
        """
        if self.predefined_id is not None:
            return self.predefined_id
        return ''.join(random.choice(chars) for _ in range(size))

    def generate_sld_name(self):
        """
        New SLD Name = Layer Name + "_" + Random id
        """
        random_id =  self.id_generator()
        return '%s_%s' % (self.layer_name, random_id)


    def format_rules_xml(self, rules_xml):
        """
        Given a XML in <Rules>...</Rules> tags, remove the outer tags

        <Rules>
            <Rule>....</Rule>
        </Rules>
        """
        if not rules_xml:
            return None

        rules_xml = rules_xml.replace(self.RULES_START_TAG, '').replace(self.RULES_END_TAG, '')

        rules_xml = self.apply_tag_prefixes(rules_xml)
        #print ('rules_xml', rules_xml)
        # Formerly parsed XML tree, etc, but this seemed a bit easier
        return rules_xml


    def get_xml_replacement_pairs(self, tag_name_list, prefix):
        """
        Format Rules returned by SLD rest service to conform to larger SLD.

        e.g. change <Rule> to <sld:Rule>
                    <PropertyIsGreaterThanOrEqualTo> to <ogc:PropertyIsGreaterThanOrEqualTo>, etc.

        """
        if tag_name_list is None or prefix is None:
            return None

        replacement_pairs = []
        for t in tag_name_list:
            replacement_pairs.append( ('<%s' % t, '<%s:%s' % (prefix,t) ) )      # start tag
            replacement_pairs.append( ('</%s>' % t, '</%s:%s>' % (prefix,t) ) )      # start tag

        return replacement_pairs

    def apply_tag_prefixes(self, rules_xml):
        if not rules_xml:
            return None

        sld_tags = ['Rule', 'Title', 'PolygonSymbolizer', 'CssParameter', 'Fill', 'Stroke']
        replace_pairs = self.get_xml_replacement_pairs(sld_tags, 'sld')

        ogc_tags = ['Filter', 'And', 'PropertyIsGreaterThanOrEqualTo', 'PropertyName', 'Literal', 'PropertyIsLessThanOrEqualTo', 'PropertyIsGreaterThan', 'PropertyIsLessThan', 'PropertyIsEqualTo']
        replace_pairs += self.get_xml_replacement_pairs(ogc_tags, 'ogc')

        for val, replace_val in replace_pairs:
            rules_xml = rules_xml.replace(val, replace_val)

        return rules_xml


    def convert_rules_to_point(self, rules_xml_formatted):
        """
        The SLD service returns styles with "PolygonSymbolizer" specs.
        For points, extra conversion is needed.
        """
        if rules_xml_formatted is None:
            add_err_msg("rules_xml_formatted cannot be None")
            return rules_xml_formatted

        if self.current_sld is None:
            add_err_msg("The current SLD cannot be None")
            return rules_xml_formatted

        start_polygon_tag = '<sld:PolygonSymbolizer>'
        end_polygon_tag = '</sld:PolygonSymbolizer>'

        start_idx = rules_xml_formatted.find(start_polygon_tag)

        while start_idx > -1:
            end_idx = rules_xml_formatted.find(end_polygon_tag, start_idx+len(start_polygon_tag))
            if end_idx == -1:
                self.add_err_msg('Could not tag in SLD: %s' % end_polygon_tag)
                return rules_xml_formatted

            polygon_chunk = rules_xml_formatted[start_idx:end_idx+len(end_polygon_tag)]

            # Pull the color from the fill parameter
            #
            m = re.findall(\
                r'<sld:CssParameter name="fill">(#[A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})</sld:CssParameter>',
                polygon_chunk)

            # Use the color and replace the PolygonSymbolizer
            #       with XML for a PointSymbolizer
            #
            if len(m) > 0:
                hex_fill_color = m[0]
                point_chunk = self.get_point_symbolizer_xml(hex_fill_color)

                rules_xml_formatted = rules_xml_formatted.replace(\
                                polygon_chunk,
                                self.get_point_symbolizer_xml(hex_fill_color))

            start_idx = rules_xml_formatted.find(start_polygon_tag)

        return rules_xml_formatted



    def get_point_symbolizer_xml(self, fill_color):
        """Return a PointSymbolizer XML chunk with the givn fill color"""

        return """<sld:PointSymbolizer>
            <sld:Graphic>
              <sld:Mark>
                <sld:Fill>
                  <sld:CssParameter name="fill">{0}</sld:CssParameter>
                </sld:Fill>
                <sld:Stroke>
                  <sld:CssParameter name="stroke">#ffffbb</sld:CssParameter>
                </sld:Stroke>
              </sld:Mark>
              <sld:Size>10</sld:Size>
            </sld:Graphic>
          </sld:PointSymbolizer>""".format(fill_color)



    def format_sld_xml(self, rules_xml):
        """
        Convert the XML rules into a full SLD
        """
        if not rules_xml:
            self.add_err_msg('You must specify the "rules_xml"')
            return False

        self.formatted_sld_xml = None

        rules_xml_formatted = self.format_rules_xml(rules_xml)
        if rules_xml_formatted is None:
            self.add_err_msg("Failed to format the XML rules (id:1)")
            return False

        if self.is_point_layer:
            rules_xml_formatted = self.convert_rules_to_point(rules_xml_formatted)

        xml_str = """<?xml version="1.0"?>
        <sld:StyledLayerDescriptor xmlns:sld="http://www.opengis.net/sld" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
            <sld:NamedLayer>
                <sld:Name>%s:%s</sld:Name>
                <sld:UserStyle>
                    <sld:Name>%s</sld:Name>
                    <sld:FeatureTypeStyle>%s</sld:FeatureTypeStyle>
                </sld:UserStyle>
            </sld:NamedLayer>
        </sld:StyledLayerDescriptor>""" % (\
                    settings.DEFAULT_WORKSPACE,
                    self.layer_name,
                    self.sld_name,
                    rules_xml_formatted)

        # For polgyons, add a stroke color.
        # If this isn't a polygon, the sld wil be returned unchanged
        #
        xml_str = self.add_polygon_stroke(xml_str)
        if xml_str is None:
            self.add_err_msg("Failed to format the XML rules (id:2)")
            return False

        self.formatted_sld_xml = remove_whitespace_from_xml(xml_str)
        if xml_str is None:
            self.add_err_msg("Failed to format the XML rules (id:3)")
            return False

        LOGGER.debug('self.formatted_sld_xml %s', self.formatted_sld_xml )

        return True


    def add_polygon_stroke(self, sld_xml_str):
        """
        The default stroke (for polygons) is:  <Stroke/>
        Update it to a lighter color.
        (If <Stroke/> isn't found, return the sld_xml_str as is)
        """
        if sld_xml_str is None:
            return None

        stroke_color = '#000000'

        no_stroke = '<sld:Stroke/>'
        default_stroke = ('<sld:Stroke>'
                          '<sld:CssParameter name="stroke">%s</sld:CssParameter>'
                          '<sld:CssParameter name="stroke-width">0.5</sld:CssParameter>'
                          '</sld:Stroke>') % stroke_color

        return sld_xml_str.replace(no_stroke, default_stroke)


    def get_test_rules(self):
        """Only used for testing"""

        return """<Rules>
          <Rule>
            <Title> &gt; -2.7786 AND &lt;= 2.4966</Title>
            <Filter>
              <And>
                <PropertyIsGreaterThanOrEqualTo>
                  <PropertyName>Violence_4</PropertyName>
                  <Literal>-2.7786</Literal>
                </PropertyIsGreaterThanOrEqualTo>
                <PropertyIsLessThanOrEqualTo>
                  <PropertyName>Violence_4</PropertyName>
                  <Literal>2.4966</Literal>
                </PropertyIsLessThanOrEqualTo>
              </And>
            </Filter>
            <PolygonSymbolizer>
              <Fill>
                <CssParameter name="fill">#424242</CssParameter>
              </Fill>
              <Stroke/>
            </PolygonSymbolizer>
          </Rule>
          <Rule>
            <Title> &gt; 13.047 AND &lt;= 18.3222</Title>
            <Filter>
              <And>
                <PropertyIsGreaterThan>
                  <PropertyName>Violence_4</PropertyName>
                  <Literal>13.047</Literal>
                </PropertyIsGreaterThan>
                <PropertyIsLessThanOrEqualTo>
                  <PropertyName>Violence_4</PropertyName>
                  <Literal>18.3222</Literal>
                </PropertyIsLessThanOrEqualTo>
              </And>
            </Filter>
            <PolygonSymbolizer>
              <Fill>
                <CssParameter name="fill">#B0B0B0</CssParameter>
              </Fill>
              <Stroke/>
            </PolygonSymbolizer>
          </Rule>
        </Rules>"""

if __name__=='__main__':
    sld_formatter = StyleRulesFormatter('layer-name')
    print (sld_formatter.format_sld_xml(sld_formatter.get_test_rules()))
