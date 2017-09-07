import psycopg2
from django.db import models
from django.db.models import signals
from geonode.base.models import ResourceBase
from geonode.layers.models import Attribute, AttributeManager
from geonode.layers.models import Layer
from django.utils.text import slugify

TRANSFORMATION_FUNCTIONS = []

class DataTable(Layer):

    """
    DataTable (inherits ResourceBase fields)
    """

    # internal fields
    table_name = models.CharField(max_length=255)
    tablespace = models.CharField(max_length=255)
    uploaded_file = models.FileField(upload_to="datatables")
    create_table_sql = models.TextField(null=True, blank=True)

    @property
    def attributes(self):
        return self.attribute_set.exclude(attribute='the_geom')

    objects = AttributeManager()

    def __unicode__(self):
        return self.table_name

    def remove_table(self):
        conn = psycopg2.connect("dbname=geonode user=geonode")
        cur = conn.cursor()
        cur.execute('drop table if exists %s;' % self.table_name)
        conn.commit()
        cur.close()
        conn.close()

class GeocodeType(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text='Examples: US Census Block, US County FIPS code, US Zip code, etc')
    description = models.CharField(max_length=255, blank=True, help_text='Short description for end user')
    sort_order = models.IntegerField(default=10)

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

    def __unicode__(self):
        return self.name

class JoinTarget(models.Model):
    """
    JoinTarget
    """

    layer = models.ForeignKey(Layer)
    attribute = models.ForeignKey(Attribute)
    geocode_type = models.ForeignKey(GeocodeType, on_delete=models.PROTECT)
    type = models.ForeignKey(JoinTargetFormatType, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)

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

class TableJoin(models.Model):
    """
    TableJoin
    """

    datatable = models.ForeignKey(DataTable)
    source_layer = models.ForeignKey(Layer, related_name="source_layer")
    table_attribute = models.ForeignKey(Attribute, related_name="table_attribute")
    layer_attribute = models.ForeignKey(Attribute, related_name="layer_attribute")
    view_name = models.CharField(max_length=255, null=True, blank=True)
    view_sql = models.TextField(null=True, blank=True)
    join_layer = models.ForeignKey(Layer, related_name="join_layer", null=True, blank=True)
    matched_records_count = models.IntegerField(null=True, blank=True)
    unmatched_records_count = models.IntegerField(null=True, blank=True)
    unmatched_records_list = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.view_name

    def remove_joins(self):
        conn = psycopg2.connect("dbname=geonode user=geonode")
        cur = conn.cursor()
        cur.execute('drop view if exists %s;' % self.view_name)
        cur.execute('drop materialized view if exists %s;' % self.view_name.replace('view_', ''))
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
