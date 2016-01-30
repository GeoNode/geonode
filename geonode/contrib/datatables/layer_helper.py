import string
from random import choice

import logging
from django.conf import settings
from django.contrib.auth.models import User

from geonode.maps.forms import TYPE_CHOICES
from geonode.maps.models import Layer, LayerAttribute
from geonode.maps.utils import get_valid_layer_name, check_projection, create_django_record
from geonode.maps.gs_helpers import get_sld_for#, get_postgis_bbox

from geonode.contrib.msg_util import *

from geoserver.catalog import Catalog
from geoserver.resource import FeatureType

from .models import DataTable, DataTableAttribute
#from .models import DataTable, DataTableAttribute, TableJoin

ATTR_TYPE_MAP = dict(boolean="java.lang.Boolean"\
                    , date="java.util.Date"\
                    , timestamp="java.util.Date"\

                    , float="java.lang.Float"\
                    , decimal="java.lang.Float"\

                    , double="java.lang.Double"\

                    , long="java.lang.Long"\

                    , int="java.lang.Integer"\

                    , unicode="java.lang.String"\
                    , string="java.lang.String"\
                    , byte="java.lang.Byte"\
                    , short="java.lang.Short"\

                )
"""
   xsd:float', u'xsd:decimal', u'xsd:int', u'xsd:double', u'gml:MultiLineStringPropertyType', u'gml:GeometryPropertyType', u'gml:MultiPolygonPropertyType', u'xsd:date', u'xsd:string', u'xsd:boolean', u'gml:PointPropertyType', u'xsd:long', u'gml:MultiPointPropertyType', u'xsd:dateTime', u'gml:LineStringPropertyType'
   #TYPE_CHOICES = (
       ('java.lang.Boolean', 'Boolean (true/false)'),
       ('java.util.Date', 'Date/Time'),
       ('java.lang.Float', 'Number (Float)'),
       ('java.lang.Integer', 'Number (Integer)'),
       ('java.lang.String', 'Text'),
        )
    """
#Map, Layer, MapLayer, Contact, ContactRole, \
#     get_csw, LayerCategory, LayerAttribute, MapSnapshot, MapStats, LayerStats, CHARSETS

logger = logging.getLogger(__name__)

'''
python manage.py shell --settings=geonode.settings

from geonode.maps.models import Layer
l = Layer.objects.all()[0]
dir(l)
'''
'''

GEOMETRY_CHOICES = [
    ['Point', 'Points'],
    ['LineString', 'Lines'],
    ['Polygon', 'Polygons (Shapes)']
]
class LayerCreateForm(forms.Form):
    name = forms.CharField(label="Name", max_length=256,required=True)
    title = forms.CharField(label="Title",max_length=256,required=True)
    srs = forms.CharField(label="Projection",initial="EPSG:4326",required=True)
    geom = forms.ChoiceField(label="Data type", choices=GEOMETRY_CHOICES,required=True)
    keywords = forms.CharField(label = '*' + ('Keywords (separate with spaces)'), widget=forms.Textarea)
    abstract = forms.CharField(widget=forms.Textarea, label="Abstract", required=True)
    permissions = JSONField()
'''

def create_geoserver_and_geonode_layers(new_table_owner, view_name, datatable, join_layer):
    """
    Creates both a GeoServer and related GeoNode Layer objects

    success:  (True, geonode.maps.models.Layer)
    fail: (False, err_msg string)
    """
    msgt('create_geoserver_and_geonode__layers 1')
    assert isinstance(datatable, DataTable), \
            "datatable must be a DataTable object, not: %s" % datatable.__class__.__name__
    assert isinstance(new_table_owner, User)\
        , "new_table_owner must a User object, not: %s" % new_table_owner.__class__.__name__
    assert isinstance(join_layer, Layer)\
        , "join_layer must be a Layer object, not: %s" % new_table_owner.__class__.__name__

    cat = Layer.objects.gs_catalog

    msg('create_geoserver_and_geonode_layers 2')

    # Assume default workspace
    ws = cat.get_workspace(settings.DEFAULT_WORKSPACE)
    if ws is None:
        err_msg = 'Specified workspace [%s] not found' % settings.DEFAULT_WORKSPACE
        return (False, err_msg)

    msg('create_geoserver_and_geonode_layers 3')

    # Assume datastore used for PostGIS
    store = settings.DB_DATASTORE_NAME
    if store is None:
        err_msg = 'Specified store [%s] not found' % settings.DB_DATASTORE_NAME
        return (False, err_msg)

    msg('create_geoserver_and_geonode_layers 4')

    """
    attribute_list = [
#        ["the_geom","com.vividsolutions.jts.geom." + layer_form.cleaned_data['geom'],{"nillable":False}],
        ["the_geom","com.vividsolutions.jts.geom.Polygon" ,{"nillable":False}],

        ["Name","java.lang.String",{"nillable":True}],
        ["Description","java.lang.String", {"nillable":True}],
        ["Start_Date","java.util.Date",{"nillable":True}],
        ["End_Date","java.util.Date",{"nillable":True}],
        ["String_Value_1","java.lang.String",{"nillable":True}],
        ["String_Value_2","java.lang.String", {"nillable":True}],
        ["Number_Value_1","java.lang.Float",{"nillable":True}],
        ["Number_Value_2","java.lang.Float", {"nillable":True}],
    ]
    """
    attribute_list = create_join_table_attribute_list(datatable)
    msg('create_geoserver_and_geonode_layers 5')

    # Add geometry to attributes dictionary, based on user input; use OrderedDict to remember order
    #attribute_list.insert(0,[u"the_geom",u"com.vividsolutions.jts.geom." + layer_form.cleaned_data['geom'],{"nillable":False}])

    name = get_valid_layer_name(view_name)
    msg('get_valid_layer_name: %s' % name)
    msg('create_geoserver_and_geonode_layers 6')

    permissions = {"anonymous":"layer_readonly","authenticated":"_none","customgroup":"_none","users":[["raman_prasad@harvard.edu","layer_admin"]]}#layer_form.cleaned_data["permissions"]

    # ------------------------------------------------------
    # Create the GeoServer FeatureType and Layer
    # ------------------------------------------------------
    new_feature_type = None
    try:
        logger.info("Create layer %s", name)
        msg('create_geoserver_and_geonode_layers 7. Create layer %s' % name)
        print 'attribute_list', attribute_list
        new_feature_type = cat.create_native_layer(settings.DEFAULT_WORKSPACE,
                                  settings.DB_DATASTORE_NAME,
                                  name,
                                  name,
                                  datatable.title,
                                  join_layer.srs,
                                  attribute_list)
        msg('LAYER 1 type: %s (%s)' % (new_feature_type.__class__.__name__, new_feature_type.name))
    except Exception, e:
        err_msg = "Failed to create the geoserver layer. \nErrors: %s" % str(e)
        logger.info(err_msg)
        msg(err_msg)
        return (False, err_msg)

    msg(dir(new_feature_type))
    for k, v in new_feature_type.__dict__.items():
        if not k.startswith('__'):
            attr_obj = eval('new_feature_type.%s' % k)
            if hasattr(attr_obj, '__call__'):
                msg('%s: [%s]' % (k, attr_obj.__call__()))
            else:
                msg('%s: [%s]' % (k, v))

    # ------------------------------------------------------
    # Set the Layer's default Style
    # ------------------------------------------------------
    logger.info("Create default style")
    set_default_style_for_new_layer(cat, new_feature_type)
    """
    new_geoserver_layer = cat.get_layer(name)
    if not new_geoserver_layer:
        err_msg = "Failed to find the new geoserver layer using name: %s" % name
        logger.info(err_msg)
        msg(err_msg)
        return (False, err_msg)

    # Does an SLD already exist?
    #
    sld = get_sld_for(new_geoserver_layer)
    if not sld:
        cat.create_style(name, sld)

        msg('create_geoserver_and_geonode_layers 9')
        new_geoserver_layer.default_style = cat.get_style(name)
        cat.save(new_geoserver_layer)
    """
    logger.info("Check projection")
    msg('check projection: %s' % check_projection(name, new_feature_type))

    logger.info("Create django record")

    keywords_str = ''
    abstract = '(abstract)'



    try:
        new_geonode_layer = create_django_record(new_table_owner\
                                    , name  #.split(':')[-1]#.title\
                                    , keywords_str.split(" ")\
                                    , abstract\
                                    , new_feature_type\
                                    , permissions\
                                    )
        msg('geonodeLayer: %s' % new_geonode_layer)
    except Exception, e:
        err_msg = 'Failed to create geonode_layer: %s' % str(e)
        logger.error(err_msg)
        return (False, err_msg)


    create_layer_attributes_from_datatable(datatable, new_geonode_layer)

    return True, new_geonode_layer


def create_join_table_attribute_list(datatable):
    """
    New joined tables (views) start with "the_geom" and then include all of the table attributes
    """
    assert isinstance(datatable, DataTable), "datatable must be a DataTable object, not '%s'" % datatable.__class__.__name__

    attribute_list = [
        ["the_geom","com.vividsolutions.jts.geom.Polygon" ,{"nillable":False}],
    ]

    for dt_attr in DataTableAttribute.objects.filter(datatable=datatable):
        java_type = ATTR_TYPE_MAP.get(dt_attr.attribute_type, None)
        if java_type is None:
            raise Exception('java type not found for datatable attribute: %s' % dt_attr)

        attr_info = [ "%s" % dt_attr, "%s" % java_type, {"nillable":True} ]
        attribute_list.append(attr_info)

    return attribute_list
    """
     ["Name","java.lang.String",{"nillable":True}],
        ["Description","java.lang.String", {"nillable":True}],
        ["Start_Date","java.util.Date",{"nillable":True}],
        ["End_Date","java.util.Date",{"nillable":True}],
        ["String_Value_1","java.lang.String",{"nillable":True}],
        ["String_Value_2","java.lang.String", {"nillable":True}],
        ["Number_Value_1","java.lang.Float",{"nillable":True}],
        ["Number_Value_2","java.lang.Float", {"nillable":True}],
    """


def set_default_style_for_new_layer(geoserver_catalog, feature_type):
    """
    For a newly created Geoserver layer in the Catalog, set a default style

    :param catalog:
    :param feature_type:

    Returns success (True,False), err_msg (if False)
    """
    assert isinstance(geoserver_catalog, Catalog)
    assert isinstance(feature_type, FeatureType)
    logger.info('set_default_style_for_new_layer')

    # ----------------------------------------------------
    # Retrieve the layer from the catalog
    # ----------------------------------------------------
    new_layer = geoserver_catalog.get_layer(feature_type.name)
    if not new_layer:
        err_msg = "New layer not found in catalog for name: %s" % feature_type.name
        logger.error(err_msg)
        return (False, err_msg)

    # ----------------------------------------------------
    # Retrieve the SLD for this layer
    # ----------------------------------------------------
    sld = get_sld_for(new_layer)
    if sld is None:
        err_msg = "SLD not found in catalog for new_layer: %s" % new_layer
        logger.error(err_msg)
        return (False, err_msg)


    # ----------------------------------------------------
    # Create a new style name
    # ----------------------------------------------------
    random_ext = "".join([choice(string.ascii_lowercase + string.digits) for i in range(4)])
    new_layer_stylename = '%s_%s' % (feature_type.name, random_ext)

    logger.info('new_layer_stylename: %s' % new_layer_stylename)

    # ----------------------------------------------------
    # Add this new style to the catalog
    # ----------------------------------------------------
    try:
        geoserver_catalog.create_style(new_layer_stylename, sld)
        msg('created!')
    except geoserver.catalog.ConflictingDataError, e:
        err_msg = (_('There is already a style in GeoServer named ') +
                        '"%s"' % (name))
        logger.error(msg)
        return False, err_msg

    # ----------------------------------------------------
    # Use the new SLD as the layer's default style
    # ----------------------------------------------------
    try:
        new_layer.default_style = geoserver_catalog.get_style(new_layer_stylename)
        geoserver_catalog.save(new_layer)
    except Exception as e:
        import traceback
        traceback.print_exc(sys.exc_info())
        err_msg = "Error setting new default style for layer. %s" % (str(e))
        #print err_msg
        logger.error(err_msg)
        return False, err_msg

    msg('default saved')
    msg('sname: %s' % new_layer.default_style )
    return True


def create_layer_attributes_from_datatable(datatable, layer):
    """
    When a new Layer has been created from a DataTable,
    Create LayerAttribute objects from the DataTable's DataTableAttribute objects
    """
    assert isinstance(datatable, DataTable), "datatable must be a Datatable object"
    assert isinstance(layer, Layer), "layer must be a Layer object"

    logger.info('create_layer_attributes_from_datatable')

    names_of_attrs = ('attribute', 'attribute_label', 'attribute_type', 'searchable', 'visible', 'display_order')

    # Iterate through the DataTable's DataTableAttribute objects
    #   - For each one, create a new LayerAttribute
    #
    for dt_attribute in DataTableAttribute.objects.filter(datatable=datatable):

        # Make key, value pairs of the DataTableAttribute's values
        new_params = dict([ (attr_name, dt_attribute.__dict__.get(attr_name)) for attr_name in names_of_attrs ])
        new_params['layer'] = layer

        # Creata or Retrieve a new LayerAttribute
        layer_attribute_obj, created = LayerAttribute.objects.get_or_create(**new_params)
        if created:
            logger.info('LayerAttribute created: %s' % layer_attribute_obj)
        else:
            logger.info('LayerAttribute exists: %s' % layer_attribute_obj)

        """
        if created:
            print 'layer_attribute_obj created: %s' % layer_attribute_obj
        else:
            print 'layer_attribute_obj EXISTS: %s' % layer_attribute_obj
        """