"""
Given Style Rules, create an SLD in XML format add it to a layer
"""
if __name__=='__main__':
    import os, sys
    DJANGO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(DJANGO_ROOT)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'

import logging
import os
from random import choice
import re
from xml.etree.ElementTree import XML, ParseError

try:
    from urlparse import urljoin
except:
    from urllib.parse import urljoin        # python 3.x

from django.utils.translation import ugettext as _
from django.conf import settings

from geonode.contrib.dataverse_connect.layer_metadata import LayerMetadata
from geonode.maps.models import Layer
from geonode.contrib.dataverse_styles.geoserver_rest_util import make_geoserver_json_put_request, make_geoserver_put_sld_request
from geonode.contrib.dataverse_styles.geonode_get_services import get_style_name_for_layer



logger = logging.getLogger("geonode.contrib.dataverse_styles.style_layer_maker")


class StyleLayerMaker:

    """
    Given Style Rules, create SLD XML and add it to a layer

    Basic usage:

    # Init object with an existing layer name
    style_layer_maker = StyleLayerMaker('income_2so')

    # Use some SLD info in XML format
    sld_xml_content = open('test_rules.xml', 'r').read()    # 'test_rules.xml' contains a SLD info in XML format

    # Add sld_xml_content to the layer as the default style
    success = style_layer_maker.add_sld_xml_to_layer(sld_xml_content)

    # If operation failed, check error messages
    if not success:
        if style_layer_maker.err_found:
            print ('\n'.join(err_msgs))

    """
    def __init__(self, layer_name):
        self.gs_catalog_obj = Layer.objects.gs_catalog
        self.layer_name = layer_name

        self.err_found = False
        self.err_msgs = []
        self.layer_metadata = None      # LayerMetadata object


    def add_err_msg(self, err_msg):
        self.err_found = True
        self.err_msgs.append(err_msg)

        logger.warn(err_msg)


    def create_layer_metadata(self, layer_name):

        if layer_name is None:
            self.layer_metadata = None
            return

        #self.layer_metadata = LayerMetadata(**dict(geonode_layer_name=layer_name))
        self.layer_metadata = LayerMetadata.create_metadata_using_layer_name(layer_name)

    def get_layer_metadata(self):
        """Return a LayerMetadata object, if it exists"""
        if self.layer_metadata:
            return None

        return self.layer_metadata


    def add_sld_to_layer(self, formatted_sld_object):

        # update layer via 2 PUT calls to the geoserver
        return self.add_sld_xml_to_layer_via_puts(formatted_sld_object,\
                self.layer_name)

        # use direct python, but doesn't properly clear tile cache
        #return self.add_sld_xml_to_layer(formatted_sld_object)

    def get_url_to_set_sld_rules(self, style_name):
        """
         Create url to set the new SLD to the layer via a put
         #http://localhost:8000/gs/rest/styles/social_disorder_nydj_k_i_v.xml

            This will be sent with a XML content containing the SLD rules
        """
        if not style_name:
            return None

        # (1) Given the layer, retrieve the SLD containing the style name
        #
        # (to do)

        # (2) Format the url for adding/retrieving styles
        #
        url_fragment = 'rest/styles/%s.xml' % (style_name)
        full_url = urljoin(settings.GEOSERVER_BASE_URL, url_fragment)

        return full_url


    def get_set_default_style_url(self, layer_name):
        """
        Given a layer name, return the REST url to set a default style
        """
        if not layer_name:
            return None

        url_fragment = 'rest/layers/%s:%s' % (settings.DEFAULT_WORKSPACE, layer_name)
        full_url = urljoin(settings.GEOSERVER_BASE_URL, url_fragment)

        return full_url


    def add_sld_xml_to_layer_via_puts(self, formatted_sld_object, layer_name):
        if not formatted_sld_object or not layer_name:
            return False

        print '-' * 40
        print 'formatted_sld_object.formatted_sld_xml'
        print formatted_sld_object.formatted_sld_xml
        print '-' * 40

        # (1) Verify the XML
        if not self.is_xml_verified(formatted_sld_object.formatted_sld_xml):
            self.add_err_msg('The style information contains invalid XML')
            return False

        # (2) Set the new SLD to the layer via a put
        #http://localhost:8000/gs/rest/styles/social_disorder_nydj_k_i_v.xml
        # --------------------------------------
        # Retrieve the style name for this layer
        # --------------------------------------
        (success, style_name_or_err_msg) = get_style_name_for_layer(layer_name)
        if not success:
            self.add_err_msg(style_name_or_err_msg)
            return False

        geoserver_sld_url = self.get_url_to_set_sld_rules(style_name_or_err_msg)
        print 'geoserver_sld_url', geoserver_sld_url
        print '-' * 40
        print 'formatted_sld_object.formatted_sld_xml', formatted_sld_object.formatted_sld_xml
        print '-' * 40
        (response, content) = make_geoserver_put_sld_request(geoserver_sld_url, formatted_sld_object.formatted_sld_xml)
        print 'response', response
        print '-' * 40
        print 'content', content
        print '-' * 40

        if response is None or not response.status == 200:
            self.add_err_msg('Failed to set new style as the default')
            return False

        # (3) Set the new style as the default for the layer
        #     Send a PUT to the catalog to set the default style
        json_str = """{"layer":{"defaultStyle":{"name":"%s"},"styles":{},"enabled":true}}""" % formatted_sld_object.sld_name
        geoserver_json_url = self.get_set_default_style_url(self.layer_name)
        if geoserver_json_url is None:
            self.add_err_msg('Failed to format the url to set new style for layer: %s' % self.layer_name)
            return False

        (response, content) = make_geoserver_json_put_request(geoserver_json_url, json_str)

        if response is None or not response.status in (200, 201):
            self.add_err_msg('Failed to set new style as the default')
            return False

        self.create_layer_metadata(self.layer_name)
        print '-' * 40
        print ('layer %s saved with style %s' % (self.layer_name, formatted_sld_object.sld_name))
        return True


    def add_sld_xml_to_layer(self, formatted_sld_object):
        """
        NOT USING, tiles were not getting refreshed properly
        Keeping code around in case needed in the future
        """
        if not formatted_sld_object:
            return False

        print 'type(formatted_sld_object)', type(formatted_sld_object)
        # (1) Verify the XML
        if not self.is_xml_verified(formatted_sld_object.formatted_sld_xml):
            self.add_err_msg('The style information contains invalid XML')
            return False

        # (2) Retrieve the layer
        layer_obj = self.gs_catalog_obj.get_layer(self.layer_name)
        if layer_obj is None:
            self.add_err_msg('The layer "%s" does not exist' % self.layer_name)
            return False

        self.show_layer_style_list(layer_obj)
        #self.clear_alternate_style_list(layer_obj)

        # (3) Create a style name
        #stylename = self.layer_name + self.get_random_suffix()
        #while self.is_style_name_in_catalog(stylename):
        #    stylename = self.layer_name + self.get_random_suffix()
        style_name = formatted_sld_object.sld_name
        # (4) Add the xml style to the catalog, with the new name
        try:
            # sync names
            self.gs_catalog_obj.create_style(style_name, formatted_sld_object.formatted_sld_xml)
        except:
            self.add_err_msg('Failed to add style to the catalog: %s' % style_name)
            return False

        # (5) Pull the style object back from the catalog
        new_style_obj = self.gs_catalog_obj.get_style(style_name)
        if new_style_obj is None:
            self.add_err_msg('Failed to find recently added style in the catalog: %s' % style_name)
            return False

        # (6) Set the new style as the default for the layer
        layer_obj.default_style = new_style_obj

        # Save it!
        try:
            self.gs_catalog_obj.save(layer_obj)
        except:
            self.add_err_msg('Failed to save new default style with layer' % (style_name))
            return False


        self.create_layer_metadata(self.layer_name)
        print ('layer %s saved with style %s' % (self.layer_name, style_name))
        return True


    def get_random_suffix(self, num_chars=4):

        return  "_".join([choice('qwertyuiopasdfghjklzxcvbnm0123456789') for i in range(num_chars)])


    def get_style_from_name(self, style_name):
        """
        Get the style object from the style name

        :returns: Style object or None
        """
        if not style_name:
            return None

        return self.gs_catalog_obj.get_style(style_name)


    def is_style_name_in_catalog(self, style_name):
        """
        Is the style name in the Catalog?
        """
        if not style_name:
            return False

        style_obj = self.get_style_from_name(style_name)
        if style_obj is None:
            return False

        return True


    def clear_alternate_style_list(self, layer_obj):
        """
        Clear existing alternate styles from layer
        (ask Matt how to delete a style)
        """

        if not layer_obj.__class__.__name__ == 'Layer':
            return False

        # clear style list
        layer_obj._set_alternate_styles([])

        # save cleared list
        self.gs_catalog_obj.save(layer_obj)
        return True


    def add_style_to_alternate_list(self, layer_obj, style_obj):
        """
        Add a layer to the alternate list, to preserve it
        """
        if not (layer_obj.__class__.__name__ == 'Layer' and style_obj.__class__.name == 'Style'):
            return False

        # get style list
        alternate_layer_style_list = layer_obj._get_alternate_styles()

        # does style already exist in list?
        if self.is_style_name_in_catalog(style_obj.name) is True:
            return False

        # add new style to list
        alternate_layer_style_list.append(style_obj)

        # update the layer with the new list
        layer_obj._set_alternate_styles(alternate_layer_style_list)

        return True
        #self.gs_catalog_obj.save(layer_obj)


    def show_layer_style_list(self, layer_obj):
        print('Show layer styles')
        if not layer_obj.__class__.__name__ == 'Layer':
            print ('not a layer', type(layer_obj))
            return

        sl = [layer_obj.default_style.name]
        for s in layer_obj._get_alternate_styles():
           sl.append(s.name)
        for idx, sname in enumerate(sl):
            if idx == 0:
                print('%s (default)' % sname)
                continue
            print (sname)

    def is_xml_verified(self, sld_xml_str):
        if not sld_xml_str:
            return False

        try:
            sldxml = XML(sld_xml_str)

            valid_url = re.compile(settings.VALID_SLD_LINKS)

            for elem in sldxml.iter(tag='{http://www.opengis.net/sld}OnlineResource'):
                if '{http://www.w3.org/1999/xlink}href' in elem.attrib:
                    link = elem.attrib['{http://www.w3.org/1999/xlink}href']
                    if valid_url.match(link) is None:
                        err_msg = "External images in your SLD file are not permitted.  Please contact us if you would like your SLD images hosted on %s" % (settings.SITENAME)
                        self.add_err_msg(err_msg)
                        return False

        except ParseError, e:
            self.add_err_msg('Your SLD file contains invalid XML')
            return False

        return True



if __name__=='__main__':


    slm = StyleLayerMaker('income_2so')
    sld_xml_content = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_rules', 'test_rules_03.xml'), 'r').read()
    slm.add_sld_xml_to_layer(sld_xml_content)
