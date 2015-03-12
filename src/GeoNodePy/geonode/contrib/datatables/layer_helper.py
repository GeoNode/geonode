import logging
from django.conf import settings
from django.contrib.auth.models User

from geonode.maps.models import Layer
from geonode.maps.utils import get_valid_layer_name, check_projection, create_django_record
from geonode.maps.gs_helpers import get_sld_for#, get_postgis_bbox

from geonode.contrib.msg_util import *

from .models import DataTable
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

def create_geoserver_layer(new_table_owner, view_name, datatable, data_store, join_layer):
    """
    success:  (True, geonode Layer)
    fail: (False, err_msg string)
    """
    msgt('create_geoserver_layer 1')
    assert isinstance(datatable, DataTable), \
            "datatable must be a DataTable object, not: %s" % datatable.__class__.__name__
    assert isinstance(new_table_owner, User)\
        , "new_table_owner must a User object, not: %s" % new_table_owner.__class__.__name__

    cat = Layer.objects.gs_catalog

    msg('create_geoserver_layer 2')

    # Assume default workspace
    ws = cat.get_workspace(settings.DEFAULT_WORKSPACE)
    if ws is None:
        err_msg = 'Specified workspace [%s] not found' % settings.DEFAULT_WORKSPACE
        return (False, err_msg)

    msg('create_geoserver_layer 3')

    # Assume datastore used for PostGIS
    store = settings.DB_DATASTORE_NAME
    if store is None:
        err_msg = 'Specified store [%s] not found' % settings.DB_DATASTORE_NAME
        return (False, err_msg)

    msg('create_geoserver_layer 4')

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
    msg('create_geoserver_layer 5')

    # Add geometry to attributes dictionary, based on user input; use OrderedDict to remember order
    #attribute_list.insert(0,[u"the_geom",u"com.vividsolutions.jts.geom." + layer_form.cleaned_data['geom'],{"nillable":False}])

    name = get_valid_layer_name(view_name)
    msg('get_valid_layer_name: %s' % name)
    msg('create_geoserver_layer 6')

    permissions = {"anonymous":"layer_readonly","authenticated":"_none","customgroup":"_none","users":[["raman_prasad@harvard.edu","layer_admin"]]}#layer_form.cleaned_data["permissions"]

    try:
        logger.info("Create layer %s", name)
        msg('create_geoserver_layer 7')
        layer = cat.create_native_layer(settings.DEFAULT_WORKSPACE,
                                  settings.DB_DATASTORE_NAME,
                                  name,
                                  name,
                                  datatable.title,
                                  join_layer.srs,
                                  attribute_list)

        logger.info("Create default style")
        publishing = cat.get_layer(name)
        msg('create_geoserver_layer 8')
        msg('publishing: %s' % publishing)

        sld = get_sld_for(publishing)
        msg('sld: %s' % sld)
        cat.create_style(name, sld)
        msg('create_geoserver_layer 9')
        publishing.default_style = cat.get_style(name)
        cat.save(publishing)

        logger.info("Check projection")
        check_projection(name, layer)

        logger.info("Create django record")

        geonodeLayer = create_django_record(new_table_owner\
                                    , datatable.title
                                    , layer_form.cleaned_data['keywords'].strip().split(" "), layer_form.cleaned_data['abstract'], layer, permissions)
        msg('geonodeLayer: %s' % geonodeLayer)

        return True, geonodeLayer
    except Exception, e:
        msg(e)
        msg('Nope! except!')
        return False, "Failed!"

    """
        #-----------------------------
        redirect_to  = reverse('data_metadata', args=[geonodeLayer.typename])
        if 'mapid' in request.POST and request.POST['mapid'] == 'tab': #if mapid = tab then open metadata form in tabbed panel
            redirect_to+= "?tab=worldmap_create_panel"
        elif 'mapid' in request.POST and request.POST['mapid'] != '': #if mapid = number then add to parameters and open in full page
            redirect_to += "?map=" + request.POST['mapid']
        return HttpResponse(json.dumps({
            "success": True,
                    "redirect_to": redirect_to}))
            except Exception, e:
                logger.exception("Unexpected error.")
                return HttpResponse(json.dumps({
                    "success": False,
                    "errors": ["Unexpected error: " + escape(str(e))]}))

        else:
            #The form has errors, what are they?
            return HttpResponse(layer_form.errors, status='500')
    """