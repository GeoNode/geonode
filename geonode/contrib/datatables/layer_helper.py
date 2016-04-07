import string
from random import choice

import logging
import traceback

from geonode.maps.models import Layer, LayerAttribute
from geonode.maps.gs_helpers import get_sld_for

from geonode.contrib.msg_util import msg

from geoserver.catalog import Catalog, ConflictingDataError
from geoserver.resource import FeatureType

from geonode.contrib.datatables.name_helper import get_random_chars
from geonode.contrib.dataverse_styles.sld_name_changer \
    import update_sld_name

from .models import DataTable, DataTableAttribute
#from .models import DataTable, DataTableAttribute, TableJoin

LOGGER = logging.getLogger(__name__)


def set_default_style_for_latlng_layer(geoserver_catalog, feature_type):
    """
    Create an SLD for a new Lat/Lng Layer

    success returns (True, None)
    fail returns (False, err_msg)
    """
    assert isinstance(geoserver_catalog, Catalog)
    assert isinstance(feature_type, FeatureType)
    LOGGER.info('set_default_style_for_latlng_layer')

    # ----------------------------------------------------
    # Retrieve the layer from the catalog
    # ----------------------------------------------------
    new_layer = geoserver_catalog.get_layer(feature_type.name)
    if not new_layer:
        err_msg = "New layer not found in catalog for name: %s" % feature_type.name
        LOGGER.error(err_msg)
        return (False, err_msg)

    # ----------------------------------------------------
    # Retrieve the SLD for this layer
    # ----------------------------------------------------
    sld = get_sld_for(new_layer)
    if sld is None:
        err_msg = "SLD not found in catalog for new_layer: %s" % new_layer
        LOGGER.error(err_msg)
        return (False, err_msg)


    # ----------------------------------------------------
    # Create a new style name
    # ----------------------------------------------------
    random_ext = get_random_chars(4)
    new_layer_stylename = '%s_%s' % (feature_type.name, random_ext)

    LOGGER.info('new_layer_stylename: %s' % new_layer_stylename)

    # ----------------------------------------------------
    # Add this new style to the catalog
    # ----------------------------------------------------
    try:
        geoserver_catalog.create_style(new_layer_stylename, sld)
        msg('created!')
    except geoserver.catalog.ConflictingDataError, e:
        err_msg = (_('There is already a style in GeoServer named ') +
                        '"%s"' % (new_layer_stylename))
        LOGGER.error(err_msg)
        return False, err_msg

    # ----------------------------------------------------
    # Use the new SLD as the layer's default style
    # ----------------------------------------------------
    try:
        new_layer.default_style = geoserver_catalog.get_style(new_layer_stylename)
        geoserver_catalog.save(new_layer)
    except Exception as e:
        traceback.print_exc(sys.exc_info())
        err_msg = "Error setting new default style for layer. %s" % (str(e))
        LOGGER.error(err_msg)
        return False, err_msg

    msg('default saved')
    msg('sname: %s' % new_layer.default_style )
    return True, None



def create_layer_attributes_from_datatable(datatable, layer):
    """
    When a new Layer has been created from a DataTable,
    Create LayerAttribute objects from the DataTable's DataTableAttribute objects
    """
    if not isinstance(datatable, DataTable):
        return (False, "datatable must be a Datatable object")
    if not isinstance(layer, Layer):
        return (False, "layer must be a Layer object")

    names_of_attrs = ('attribute', 'attribute_label', 'attribute_type', 'searchable', 'visible', 'display_order')

    # Iterate through the DataTable's DataTableAttribute objects
    #   - For each one, create a new LayerAttribute
    #
    new_layer_attributes= []
    for dt_attribute in DataTableAttribute.objects.filter(datatable=datatable):

        # Make key, value pairs of the DataTableAttribute's values
        new_params = dict([ (attr_name, dt_attribute.__dict__.get(attr_name)) for attr_name in names_of_attrs ])
        new_params['layer'] = layer

        # Create or Retrieve a new LayerAttribute
        layer_attribute_obj, created = LayerAttribute.objects.get_or_create(**new_params)
        if not layer_attribute_obj:
            LOGGER.error("Failed to create LayerAttribute for: %s" % dt_attribute)
            return (False, "Failed to create LayerAttribute for: %s" % dt_attribute)

        # Add to list of new attributes
        new_layer_attributes.append(layer_attribute_obj)
        """
        if created:
            print 'layer_attribute_obj created: %s' % layer_attribute_obj
        else:
            print 'layer_attribute_obj EXISTS: %s' % layer_attribute_obj
        """
    return (True, "All LayerAttributes created")


def set_style_for_new_join_layer(geoserver_catalog, feature_type, original_layer):
    """
    Make a new SLD for a TableJoin.
    (1) Get the SLD from the original_layer layer
    (2) Add the name of the new layer

    success returns (True, None)
    fail returns (False, err_msg)

    """
    assert isinstance(geoserver_catalog, Catalog)
    assert isinstance(feature_type, FeatureType)
    assert isinstance(original_layer, Layer)

    # Ah...was the original good enough?
    #return set_default_style_for_latlng_layer(geoserver_catalog, feature_type)


    # ----------------------------------------------------
    # Get the SLD from the original layer
    # ----------------------------------------------------
    if original_layer.default_style is None:
        err_msg = ('Failed to retrieve the default_style '
                    'for the original_layer "%s" (id: %s)' %\
                    original_layer.name,
                    original_layer.id)

        LOGGER.error(err_msg)
        return False, err_msg

    #msg('orig layer style name: %s' % original_layer.default_style.name)
    original_sld = original_layer.default_style.sld_body
    if original_sld is None:
        err_msg = 'Failed to retrieve the SLD for the original_layer (id: %s)' % original_layer.id
        LOGGER.error(err_msg)
        return False, err_msg

    # ----------------------------------------------------
    # Retrieve the new layer from the catalog
    # ----------------------------------------------------
    #msg('feature_type.name: %s' % feature_type.name)

    new_layer = geoserver_catalog.get_layer(feature_type.name)
    if new_layer is None:
        err_msg = ('Failed to retrieve the Layer '
                    ' based on the feature_type '
                    ' name ("%s")' % feature_type.name)
        LOGGER.error(err_msg)
        return False, err_msg

    # ----------------------------------------------------
    # Create a new style name and
    # use it in the original_sld string
    # ----------------------------------------------------

    new_sld = update_sld_name(original_sld, new_layer.name)

    # ----------------------------------------------------
    # Add this new style to the catalog
    # ----------------------------------------------------
    random_ext = get_random_chars(4)
    new_layer_stylename = '%s_%s' % (feature_type.name, random_ext)

    try:
        geoserver_catalog.create_style(new_layer_stylename, new_sld)
        msg('created!')
    except ConflictingDataError, e:
        err_msg = (_('There is already a style in GeoServer named ') +
                        '"%s"' % (new_layer_stylename))
        LOGGER.error(err_msg)
        return False, err_msg

    # ----------------------------------------------------
    # Use the new SLD as the layer's default style
    # ----------------------------------------------------
    try:
        new_layer.default_style = geoserver_catalog.get_style(new_layer_stylename)
        geoserver_catalog.save(new_layer)
    except Exception as e:
        traceback.print_exc(sys.exc_info())
        err_msg = "Error setting new default style for layer. %s" % (str(e))
        #print err_msg
        LOGGER.error(err_msg)
        return False, err_msg

    msg('default saved')
    msg('sname: %s' % new_layer.default_style )
    return True, None
