if __name__=='__main__':
    import os, sys
    DJANGO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(DJANGO_ROOT)
    sys.path.append('/Users/rmp553/Documents/iqss-git/shared-dataverse-information')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'

import logging
from django.conf import settings
from django import forms

from shared_dataverse_information.map_layer_metadata.forms import WorldMapToGeoconnectMapLayerMetadataValidationForm
from geonode.maps.models import Layer
#from geonode.contrib.dataverse_connect.dv_utils import remove_whitespace_from_xml, MessageHelperJSON
import json

logger = logging.getLogger("geonode.contrib.dataverse_connect.layer_metadata")

"""
For a layer, add attribute metadata + download links

(1a)  layer_obj.attribute_set.all()

(1b) see maps.models: class LayerAttribute(models.Model):
    attribute = models.CharField(_('Attribute Name'), max_length=255, blank=False, null=True, unique=False)
    attribute_label = models.CharField(_('Attribute Label'), max_length=255, blank=False, null=True, unique=False)
    attribute_type = models.CharField(_('Attribute Type'), max_length=50, blank=False, null=False, default='xsd:string', unique=False)
    display_order = models.IntegerField(_('Display Order'), default=1)
    in_gazetteer = models.BooleanField(_('In Gazetteer?'), default=False)
    is_gaz_start_date = models.BooleanField(_('Gazetteer Start Date'), default=False)
    is_gaz_end_date = models.BooleanField(_('Gazetteer End Date'), default=False)

(2) layer_obj.download_links()

http://worldmap.harvard.edu/download/wms/14708/png?layers=geonode%3Apower_plants_enipedia_jan_2014_kvg&width=948
&bbox=76.04800165%2C18.31860358%2C132.0322222%2C50.78441&
service=WMS&format=image%2Fpng&
srs=EPSG
%3A4326&request=GetMap&height=550

"""

class LayerMetadata:
    """
    Prepare Layer Metadata to send back to Geoconnect, and then the Dataverse.

    For consistency between apps, use the WorldMapToGeoconnectMapLayerMetadataValidationForm

    In this case, Map Layer Metadata:
        (1) Gathered/Formatted in a dict
        (2) Validated by the WorldMapToGeoconnectMapLayerMetadataValidationForm
        (3) cleaned_data is returned
    """

    # Used to initialize this class
    METADATA_ATTRIBUTES = WorldMapToGeoconnectMapLayerMetadataValidationForm.base_fields.keys()


    def __init__(self, geonode_layer_object):
        """

        :param geonode_layer_object: Layer object
        """
        assert type(geonode_layer_object) is Layer, "geonode_layer_object must be a Layer"

        # Initialize attributes
        for attr in self.METADATA_ATTRIBUTES:
            self.__dict__[attr] = None      # kwargs.get(attr, None)

        self.update_metadata_with_layer_object(geonode_layer_object)


    @staticmethod
    def create_metadata_using_layer_name(layer_name):
        assert layer_name is not None, "layer_name must be the name of a Layer object"

        try:
            layer_obj = Layer.objects.get(name=layer_name)
        except Layer.DoesNotExist:
            logger.error("Layer not found in database for name: %s" % layer_name)
            raise LookupError("Layer not found for name: %s" % layer_name)

        return LayerMetadata(layer_obj)\


    def get_metadata_dict(self, as_json=False):

        params = {}
        for attr in self.METADATA_ATTRIBUTES:
            params[attr] = self.__dict__.get(attr, None)

        f = WorldMapToGeoconnectMapLayerMetadataValidationForm(params)
        if not f.is_valid():
            err_msg = ('Validation failed for the '
                    'WorldMapToGeoconnectMapLayerMetadataValidationForm. '
                    '\nErrors: %s' % f.errors)
            raise forms.ValidationError(err_msg)

        '''
        print '-'
        for k, v in params.items():
            print '%s: (%s)' % (k, v)
        print '-'
        '''
        
        if as_json:
            try:
                return json.dumps(params)
            except:
                err_msg = 'Failed to convert metadata to JSON'
                raise ValueError(err_msg)

        return params

    def get_attribute_metadata(self, layer_obj):
        """
        Format metadata about a layer's attributes/fields

        [ {"name": "STATE", "display_name"="State", "type": "String"}\
        , {"name": "UniqueID", "display_name"="UniqueID", "type": "Double"}\
        etc.
        ]
        """
        assert type(layer_obj) is Layer, "layer_obj must be a Layer"

        attr_info = [ dict(name=info.attribute\
                                    , display_name=info.attribute_label\
                                    , type=info.attribute_type.replace('xsd:', ''))\
                    for info in layer_obj.attribute_set.all().order_by('display_order')\
                                ]
        try:
            return json.dumps(attr_info)
        except:
            raise ValueError('JSON dump failed for attribute info')


    def update_metadata_with_layer_object(self, layer_obj):
        if not type(layer_obj) is Layer:
            return False

        self.layer_name = layer_obj.typename
        self.layer_link = '%sdata/%s' % (settings.SITEURL, layer_obj.typename)

        self.embed_map_link =  '%smaps/embed/?layer=%s' % (settings.SITEURL, layer_obj.typename)


        self.llbbox = layer_obj.llbbox
        #self.srs = layer_obj.srs
        self.attribute_info = self.get_attribute_metadata(layer_obj)
        if layer_obj.owner:
            self.worldmap_username =  layer_obj.owner.username

        download_links_dict = self.format_download_links(layer_obj)
        if download_links_dict:
            try:
                self.download_links = json.dumps(download_links_dict)
            except:
                logger.error('JSON dump failed for download links')
                logger.error('download_links_dict data: %s' % download_links_dict)
                raise ValueError('JSON dump failed for download links')
            if download_links_dict.has_key('png'):
                self.map_image_link = download_links_dict['png']

        return True

    def format_download_links(self, layer_obj):
        assert type(layer_obj) is Layer, "layer_obj must be type Layer"

        if not hasattr(layer_obj, 'resource'):
            return None
        if not hasattr(layer_obj.resource, 'resource_type'):
            return None

        link_tuples = layer_obj.download_links()
        if not link_tuples:
            return None

        link_dict = {}
        for lt in link_tuples:
            if lt and len(lt)==3:
                link_dict[lt[0]] = lt[2]
        if len(link_dict) == 0:
            return None

        return link_dict
        #try:
        #    return json.dumps(link_dict)
        #except:
        #    logger.error('JSON dump failed for download_links')
        #    logger.error('link data: %s' % link_dict)
        #    raise ValueError('JSON dump failed for download_links')


if __name__=='__main__':
    layers = Layer.objects.all()
    print 'layers', layers
    layer=None
    try:
        layer = Layer.objects.get(name='social_disorder_in_boston_yqh_zip_m3c')
    except Layer.DoesNotExist:
        print 'layer does not exist'
    if layer:
        print type(layer)
        print dir(layer)
        print layer.owner.username
        #lm = LayerMetadata(layer)
        #print lm.get_metadata_dict()

        #print '-'*40
        #print layer.download_links()

        lm = LayerMetadata.create_metadata_using_layer_name(layer.name)
        print lm.get_metadata_dict(as_json=True)
