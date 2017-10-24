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
import sys
import json
import logging
import psycopg2

from django.conf import settings
from geoserver.catalog import FailedRequestError

from geonode.contrib.datatables.db_helper import get_connection_string_via_settings
from geonode.maps.models import Layer

from geonode.contrib.dataverse_connect.dv_utils import MessageHelperJSON
from geonode.contrib.dataverse_styles.style_layer_maker import StyleLayerMaker
from geonode.contrib.dataverse_styles.style_rules_formatter import StyleRulesFormatter
from geonode.contrib.dataverse_styles.geonode_get_services import get_sld_rules
from geonode.contrib.dataverse_styles.sld_helper_form import SLDHelperForm
from geoserver.catalog import Catalog
from geonode.contrib.dataverse_connect.layer_metadata import LayerMetadata

LOGGER = logging.getLogger(__name__)

class StyleOrganizer(object):
    """
    Given a set of styling parameters, set a new style for a layer
    """
    def __init__(self, styling_params):
        self.styling_params = styling_params
        self.layer_name = styling_params.get('layer_name', None)
        self.err_found = False
        self.err_msgs = []
        self.layer_metadata = None

        self.current_sld = None
        self.is_point_layer = False

        self.check_current_sld()

    def check_current_sld(self):
        """Check the geometry via the database to see
        if the layer is a POINT or POLYGON
        """
        if self.layer_name is None:
            self.add_err_msg("The layer name was not given.")
            return False

        # --------------------------------
        # Retrieve the Layer
        # --------------------------------
        try:
            layer = Layer.objects.get(name=self.layer_name)
        except Layer.DoesNotExist:
            self.add_err_msg(('The layer with name "%s"'
                              ' was not found.') % self.layer_name)
            return False

        # --------------------------------
        # Check if this is POINT geometry
        #   via the database
        # --------------------------------
        success, conn_str_or_err = get_connection_string_via_settings(\
                            'wmdata',
                            **dict(NAME=layer.store))
        if not success:
            self.add_err_msg(conn_str_or_err)
            return False

        try:
            sql_str = ('select type from geometry_columns'
                       ' where f_table_name = \'%s\';')\
                       % layer.typename.split(':')[-1]

            conn = psycopg2.connect(conn_str_or_err)
            cur = conn.cursor()
            cur.execute(sql_str)
            data_type = cur.fetchone()[0]
            if data_type in ['POINT']:
                self.is_point_layer = True
            else:
                self.is_point_layer = False

        except Exception as ex_obj:
            traceback.print_exc(sys.exc_info())
            err_msg = ('Error finding geometry type'
                       ' for layer: %s [id: %s]')
            LOGGER.error(err_msg)
            LOGGER.error(ex_obj)
            return False
        finally:
            if conn:
                conn.close()

        # --------------------------------
        # If this is a POINT layer,
        # retrieve the SLD body
        # --------------------------------
        if self.is_point_layer is True:

            if not (layer.default_style and layer.default_style.sld_body):
                self.add_err_msg(('The default style for layer "%s"'
                                  ' was not found.') % self.layer_name)
                return False

            sld_body = layer.default_style.sld_body

            #if self.is_point_layer is False:
            #    if sld_body.find('<sld:PointSymbolizer>') > -1:
            #        self.is_point_layer = True

            self.current_sld = sld_body

        return True



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
        """Run through the layer styling steps"""

        if self.err_found:
            return False

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

        # used for error messages
        param_err = SLDHelperForm.get_style_error_message(\
                    self.styling_params.get('attribute', '(missing)'),
                    self.styling_params.get('method', '(missing)'))

        resp_json = get_sld_rules(self.styling_params)
        resp_dict = self.get_json_as_dict(\
                        resp_json,
                        '%s (sld:1)' % param_err)

        if not resp_dict.get('success') is True:
            user_msg = '%s (sld:2)' % param_err
            self.add_err_msg(user_msg)
            for err_msg in resp_dict.get('data', []):
                self.add_err_msg(err_msg)
            return None

        # (1a) Pull layer name from initial params, should not
        # fail b/c params have been evaluated in (1)
        #
        self.layer_name = self.styling_params.get('layer_name', None)
        if self.layer_name is None:
            # Layer name is not in the parameters
            self.add_err_msg('%s (sld:2)' % param_err)
            return None

        sld_rule_data = resp_dict.get('data', {}).get('style_rules', None)
        if sld_rule_data is None:
            # Failed to find rules in response'
            self.add_err_msg('%s (sld:3)' % param_err)
            return None

        num_filters = sld_rule_data.count('<Filter>')

        if num_filters > 100:
            user_msg = ('%s<br /><br />'
                        'This combination created'
                        ' %d categories but the limit'
                        ' is 100. (sld:4)') %\
                        (param_err, num_filters)
            self.add_err_msg(user_msg)
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


        # --------------------------------------
        # Create a StyleRulesFormatter object
        # --------------------------------------
        extra_kwargs = {}
        if self.is_point_layer:
            extra_kwargs = dict(is_point_layer=True,
                                current_sld=self.current_sld)

        sld_formatter = StyleRulesFormatter(self.layer_name,
                                            **extra_kwargs)
        #, style_name_or_err_msg)

        sld_formatter.format_sld_xml(sld_rule_data)

        if sld_formatter.err_found:
            LOGGER.error('ERROR: %s', sld_formatter.err_msgs)
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
        try:
            server_resp = geoserver_catalog.save(the_layer)
            print ('------server_resp----\n', server_resp)
        except FailedRequestError as fail_obj:
            # Attempt to restore previous SLD
            self.restore_old_sld(the_layer)
            #
            self.add_err_msg("Failed to add a new style.  Error: %s" % fail_obj.message)
            return False
        except:
            # Attempt to restore previous SLD
            self.restore_old_sld(the_layer)
            #
            err_msg = "Unexpected error: %s" % sys.exc_info()[0]
            self.add_err_msg("Failed to add the new style.  Error: %s" % err_msg)
            return False

        self.layer_metadata = LayerMetadata.create_metadata_using_layer_name(self.layer_name)
        return True

    def restore_old_sld(self, the_layer):
        """Attempt to restore old SLD if classification goes bad"""
        if not the_layer:
            LOGGER.error('Could not restore the old SLD. (res:1)')
            return None

        if not self.current_sld:
            LOGGER.error('Could not restore the old SLD. (res:2)')
            return False

        the_layer.default_style.update_body(self.current_sld)
        try:
            geoserver_catalog.save(the_layer)
            return True
        except FailedRequestError as fail_obj:
            LOGGER.error(\
                    "Could not restore the old SLD. %s (res:3)"\
                        % fail_obj.message)
            return False
        except:
            LOGGER.error('Could not restore the old SLD. (res:4)')
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
        LOGGER.error('\n'.join(style_organizer.err_msgs))
    #else:
    #    print ('Yes!')
    #    metadata = ls.layer_metadata
    #    if metadata:
    #        print (metadata.get_metadata_dict())
    LOGGER.debug(style_organizer.get_json_message())
