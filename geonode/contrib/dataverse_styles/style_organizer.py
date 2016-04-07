"""
Convenience class used to style a Layer via an API call.

For the workflow, see the "StyleOrganizer.style_layer()" function

API attributes include:
    datafile_id = models.IntegerField()
    dataverse_installation_name = models.CharField(max_length=255)
    layer_name = models.CharField(max_length=255)
    attribute = models.CharField(max_length=255)
    intervals = models.IntegerField()
    method = models.CharField(max_length=255)
    ramp = models.CharField(max_length=255)
    startColor = models.CharField(max_length=30)
    endColor = models.CharField(max_length=30)
    reverse = models.BooleanField(default=False)
"""
from __future__ import print_function

import json
import logging

from django.conf import settings

from geonode.contrib.dataverse_connect.dv_utils import MessageHelperJSON
from geonode.contrib.dataverse_styles.style_layer_maker import StyleLayerMaker
from geonode.contrib.dataverse_styles.style_rules_formatter import StyleRulesFormatter
from geonode.contrib.dataverse_styles.geonode_get_services import get_sld_rules
from geoserver.catalog import Catalog
from geonode.contrib.dataverse_connect.layer_metadata import LayerMetadata

LOGGER = logging.getLogger("geonode.contrib.dataverse_styles.style_organizer")

class StyleOrganizer(object):
    """
    Given a set of styling parameters, set a new style for a layer
    """
    def __init__(self, styling_params):
        self.styling_params = styling_params
        self.layer_name = None
        self.err_found = False
        self.err_msgs = []
        self.layer_metadata = None


    def add_err_msg(self, err_msg):
        """
        Add error message
        """
        self.err_found = True
        self.err_msgs.append(err_msg)
        LOGGER.warn(err_msg)


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

        # (2) Format rules into full SLD ... the SLD is XML in string format
        #
        formatted_sld_object = self.format_rules_into_full_sld(sld_rule_data)
        if formatted_sld_object is None:
            return False

        # (3) Add new SLD to Layer
        #
        #return self.add_new_sld_to_layer_orig(formatted_sld_object)
        return self.add_new_sld_to_layer(formatted_sld_object)


    def set_layer_name_and_get_rule_data(self):
        """
        (1) Check params and create rules
        """
        #print ('set_layer_name_and_get_rule_data 1')
        if self.styling_params is None:
            return None
        resp_json = get_sld_rules(self.styling_params)
        resp_dict = self.get_json_as_dict(resp_json, 'Failed to make the SLD rules')

        if not resp_dict.get('success') is True:
            user_msg = resp_dict.get('message',)
            self.add_err_msg(user_msg)
            for err_msg in resp_dict.get('data', []):
                self.add_err_msg(err_msg)
            return None

        # (1a) Pull layer name from initial params, should not
        # fail b/c params have been evaluated in (1)
        #
        self.layer_name = self.styling_params.get('layer_name', None)
        if self.layer_name is None:
            self.add_err_msg('Layer name is not in the parameters')
            return None

        sld_rule_data = resp_dict.get('data', {}).get('style_rules', None)
        if sld_rule_data is None:
            self.add_err_msg('Failed to find rules in response')
            return None

        #print ('sld_rule_data', sld_rule_data)
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


        # --------------------------------------
        # Create a StyleRulesFormatter object
        # --------------------------------------
        sld_formatter = StyleRulesFormatter(self.layer_name)#, style_name_or_err_msg)

        sld_formatter.format_sld_xml(sld_rule_data)

        if sld_formatter.err_found:
            self.add_err_msg('Failed to format xml')
            if sld_formatter.err_found:
                self.add_err_msg('\n'.join(sld_formatter.err_msgs))
            return None


        return sld_formatter


    def add_new_sld_to_layer(self, formatted_sld_object):
        """
        (3) Add new SLD to Layer
        """
        # get the catalog
        geoserver_catalog = Catalog(settings.GEOSERVER_BASE_URL + "rest",\
                    settings.GEOSERVER_CREDENTIALS[0],\
                    settings.GEOSERVER_CREDENTIALS[1])

        # pull the layer
        the_layer = geoserver_catalog.get_layer(self.layer_name)

        # set the new style
        the_layer.default_style.update_body(formatted_sld_object.formatted_sld_xml)

        # save it
        geoserver_catalog.save(the_layer)

        self.layer_metadata = LayerMetadata.create_metadata_using_layer_name(self.layer_name)
        return True


    def add_new_sld_to_layer_orig(self, formatted_sld_object):
        """
        'Legacy': Simpler code implemented in "add_new_sld_to_layer"
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
        """
        Retrieve message in JSON format
        """
        if self.layer_metadata is not None:
            metadata_dict = self.layer_metadata.get_metadata_dict()
            if metadata_dict:
                return MessageHelperJSON.get_json_msg(success=True, msg='', data_dict=metadata_dict)
            else:
                err_msg = ('StyleOrganizer. Failed to retrieve '
                            ' metadata dict for layer [%s]' %\
                            (self.layer_name))
                LOGGER.error(err_msg)
                return MessageHelperJSON.get_json_msg(success=False,\
                    msg='Fail to create format layer metadata')

        err_msg = '\n'.join(self.err_msgs)
        if not err_msg:
            err_msg = 'Failed to create layer.  Please try again'

        return MessageHelperJSON.get_json_msg(success=False, msg=err_msg)


if __name__ == '__main__':
    #from geonode_get_services import get_layer_features_definition
    layer_name = 'japan_evac_zones_se1'
    #print (get_layer_features_definition(layer_name))

    d = dict(layer_name=layer_name,\
                attribute='Socdis_202',\
                method='quantile',\
                intervals=3,\
                ramp='Random',\
                startColor='#fff5f0',\
                endColor='#67000d',\
                reverse='',\
            )
    style_organizer = StyleOrganizer(d)
    styler_succeeded = style_organizer.style_layer()
    if not styler_succeeded:
        print ('\n'.join(style_organizer.err_msgs))
    #else:
    #    print ('Yes!')
    #    metadata = ls.layer_metadata
    #    if metadata:
    #        print (metadata.get_metadata_dict())
    print ('-'*40)
    print (style_organizer.get_json_message())
