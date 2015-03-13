import psycopg2
from django.db import models
from django.db.models import signals
#from geonode.maps.models import ResourceBase
from geonode.maps.models import LayerAttribute, LayerAttributeManager
from geonode.maps.models import Layer
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _


from .db_helper import get_datastore_connection_string

TRANSFORMATION_FUNCTIONS = []


class DataTableAttributeManager(models.Manager):
    """Helper class to access filtered attributes
    """
    def visible(self):
        return self.get_query_set().filter(visible=True).order_by('display_order')


class DataTable(models.Model):

    """
    DataTable (inherits ResourceBase fields)
    """
    title = models.CharField('title', max_length=255)

    # internal fields
    table_name = models.CharField(max_length=255, unique=True)
    tablespace = models.CharField(max_length=255)
    uploaded_file = models.FileField(upload_to="datatables")
    create_table_sql = models.TextField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified =models.DateTimeField(auto_now=True)

    @property
    def attributes(self):
        return self.attribute_set.exclude(attribute='the_geom')
    objects = DataTableAttributeManager()

    def __unicode__(self):
        return self.table_name

    def remove_table(self):
        #conn = psycopg2.connect("dbname=geonode user=geonode")
        conn = psycopg2.connect(get_datastore_connection_string())
        cur = conn.cursor()
        cur.execute('drop table if exists %s;' % self.table_name)
        conn.commit()
        cur.close()
        conn.close() 


class DataTableAttribute(models.Model):
    objects = DataTableAttributeManager()
    
    #layer = models.ForeignKey(Layer, blank=False, null=False, unique=False, related_name='attribute_set')
    datatable = models.ForeignKey(DataTable, unique=False, related_name='attribute_set')
    
    attribute = models.CharField(_('Attribute Name'), max_length=255, blank=False, null=True, unique=False)
    attribute_label = models.CharField(_('Attribute Label'), max_length=255, blank=False, null=True, unique=False)
    attribute_type = models.CharField(_('Attribute Type'), max_length=50, blank=False, null=False, default='xsd:string', unique=False)
    searchable = models.BooleanField(_('Searchable?'), default=False)
    visible = models.BooleanField(_('Visible?'), default=True)
    display_order = models.IntegerField(_('Display Order'), default=1)

    #in_gazetteer = models.BooleanField(_('In Gazetteer?'), default=False)
    #is_gaz_start_date = models.BooleanField(_('Gazetteer Start Date'), default=False)
    #is_gaz_end_date = models.BooleanField(_('Gazetteer End Date'), default=False)
    #date_format = models.CharField(_('Date Format'), max_length=255, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    modified =models.DateTimeField(auto_now=True)

    
    def __str__(self):
        return "%s" % self.attribute

    def __unicode__(self):
        return self.attribute



class GeocodeType(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text='Examples: US Census Block, US County FIPS code, US Zip code, etc')
    description = models.CharField(max_length=255, blank=True, help_text='Short description for end user')
    sort_order = models.IntegerField(default=10)

    created = models.DateTimeField(auto_now_add=True)
    modified =models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('sort_order', 'name')

class JoinTargetFormatType(models.Model):
    name = models.CharField(max_length=255, help_text='Census Tract (6 digits, no decimal)') 
    description_shorthand = models.CharField(max_length=255, help_text='dddddd') 
    clean_steps = models.TextField(help_text='verbal description. e.g. Remove non integers. Check for empty string. Pad with zeros until 6 digits.')
    regex_replacement_string = models.CharField(help_text='"[^0-9]"; Usage: re.sub("[^0-9]", "", "1234.99"'\
                                , max_length=255)
    python_code_snippet = models.TextField(blank=True)
    tranformation_function_name = models.CharField(max_length=255, blank=True, choices=TRANSFORMATION_FUNCTIONS)

    created = models.DateTimeField(auto_now_add=True)
    modified =models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

class JoinTarget(models.Model):
    """
    JoinTarget
    """

    layer = models.ForeignKey(Layer)
    attribute = models.ForeignKey(LayerAttribute)
    geocode_type = models.ForeignKey(GeocodeType, on_delete=models.PROTECT)
    type = models.ForeignKey(JoinTargetFormatType, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified =models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.layer.title

    def as_json(self):
        if self.type:
            type = {'name':self.type.name, 'description':self.type.description_shorthand, 'clean_steps':self.type.clean_steps}
        else:
            type = None
        return dict(
            id=self.id, layer=self.layer.typename,
            attribute={'attribute':self.attribute.attribute, 'type':self.attribute.attribute_type},
            type=type,
            geocode_type=self.geocode_type.name)

class TableLatLngMapping(models.Model):
    datatable = models.ForeignKey(DataTable)

    lat_attribute = models.ForeignKey(DataTableAttribute, related_name="lat_attribute")
    lng_attribute = models.ForeignKey(DataTableAttribute, related_name="lng_attribute")

    layer = models.ForeignKey(Layer, related_name="mapped_layer", null=True, blank=True)

    mapped_record_count = models.IntegerField(default=0, help_text='Records mapped')
    unmapped_record_count = models.IntegerField(default=0, help_text='Records that failed to map Lat/Lng')
    unmapped_records_list = models.TextField(blank=True, help_text='Unmapped records')

    created = models.DateTimeField(auto_now_add=True)
    modified =models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Table Latitude/Longitude Mapping'

class TableJoin(models.Model):
    """
    TableJoin 
    """
    datatable = models.ForeignKey(DataTable)
    table_attribute = models.ForeignKey(DataTableAttribute, related_name="table_attribute")

    source_layer = models.ForeignKey(Layer, related_name="source_layer")
    layer_attribute = models.ForeignKey(LayerAttribute, related_name="layer_attribute")

    view_name = models.CharField(max_length=255, null=True, blank=True)
    view_sql = models.TextField(null=True, blank=True)

    join_layer = models.ForeignKey(Layer, related_name="join_layer", null=True, blank=True)

    matched_records_count = models.IntegerField(null=True, blank=True)
    unmatched_records_count = models.IntegerField(null=True, blank=True)
    unmatched_records_list = models.TextField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified =models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.view_name

    def remove_joins(self):
        conn = psycopg2.connect(get_datastore_connection_string())
        cur = conn.cursor()
        cur.execute('drop view if exists %s;' % self.view_name)
        #cur.execute('drop materialized view if exists %s;' % self.view_name.replace('view_', ''))
        conn.commit()
        cur.close()
        conn.close() 

    def as_json(self):
        return dict(
            id=self.id, datable=self.datatable.table_name, source_layer=self.source_layer.typename, join_layer=self.join_layer.typename,
            table_attribute={'attribute':self.table_attribute.attribute, 'type':self.table_attribute.attribute_type},
            layer_attribute={'attribute':self.layer_attribute.attribute, 'type':self.layer_attribute.attribute_type},
            view_name=self.view_name, 
            matched_records_count=self.matched_records_count,
            unmatched_records_count=self.unmatched_records_count,
            unmatched_records_list=self.unmatched_records_list)

def pre_delete_datatable(instance, sender, **kwargs):
    """
    Remove the table from the Database
    """
    instance.remove_table()    


def pre_delete_tablejoin(instance, sender, **kwargs):
    """
    Remove the existing join in the database
    """
    instance.remove_joins()

signals.pre_delete.connect(pre_delete_tablejoin, sender=TableJoin)
signals.pre_delete.connect(pre_delete_datatable, sender=DataTable)
