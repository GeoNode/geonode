import psycopg2
import json
from django.db import models
from django.db.models import signals

from geonode.maps.models import LayerAttribute, LayerAttributeManager
from geonode.maps.models import Layer
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from .db_helper import get_datastore_connection_string
from geonode.contrib.datatables.utils_joins import drop_view_by_name

TRANSFORMATION_FUNCTIONS = []


class DataTableAttributeManager(models.Manager):
    """
    Helper class to access filtered attributes
    """
    def visible(self):
        return self.get_query_set().filter(visible=True).order_by('display_order')


class DataTable(models.Model):

    """
    DataTable
    """
    title = models.CharField('title', max_length=255)
    abstract = models.TextField('abstract', blank=True)

    delimiter = models.CharField(max_length=6, default='')

    owner = models.ForeignKey(User, blank=True, null=True)

    # internal fields
    table_name = models.CharField(max_length=255, unique=True)
    tablespace = models.CharField('database', max_length=255) # not the actual tablespace, but the database

    uploaded_file = models.FileField(upload_to='datatables/%Y/%m/%d')
    create_table_sql = models.TextField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified =models.DateTimeField(auto_now=True)



    """python manage.py shell
from geonode.contrib.datatables.models import DataTable
dt = DataTable.objects.all()[0]
dt.as_json()
"""

    def attributes_as_json(self):
        """
        Return list of attributes as json
        (uses DataTableAttribute.as_json)
        """
        json_list = []
        for attr in self.attributes.all():
            json_list.append(attr.as_json())
        return json_list


    @property
    def attributes(self):
        return self.attribute_set.exclude(attribute='the_geom')
    objects = DataTableAttributeManager()

    def get_attribute_by_name(self, attr_name):
        """
        Return a DataTable attribute or None
        """
        if attr_name is None:
            return None

        try:
            return self.attribute_set.get(attribute=attr_name)
        except DataTableAttribute.DoesNotExist:
            return None


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

    def as_json(self):
        return dict(name=self.attribute,
                    type=self.attribute_type,
                    display_name=self.attribute_label)

    def __str__(self):
        return "%s" % self.attribute

    def __unicode__(self):
        return self.attribute



class GeocodeType(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text='Examples: US Census Block, US County FIPS code, US Zip code, etc')
    description = models.CharField(max_length=255, blank=True, help_text='Short description for end user')
    sort_order = models.IntegerField(default=10)

    slug = models.SlugField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified =models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # create the slug
        if self.name:
            self.slug = slugify(self.name)

        super(GeocodeType, self).save(*args, **kwargs)


    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('sort_order', 'name')

class JoinTargetFormatType(models.Model):
    """
    This information is sent via API and can be used to specify
    the expected data format from the client.

    For example, a census TRACT may require 6 digits, zero padded if needed

    Currently, data cleaning is NOT done on the WorldMap side.
    """
    name = models.CharField(max_length=255, help_text='Census Tract (6 digits, no decimal)')

    is_zero_padded = models.BooleanField(default=False)
    expected_zero_padded_length = models.IntegerField(default=-1)

    description = models.TextField(help_text='verbal description for client. e.g. Remove non integers. Check for empty string. Pad with zeros until 6 digits.')


    regex_match_string = models.CharField(max_length=255, blank=True,\
            help_text="""r'\\d{6}'; Usage: re.search(r'\\d{6}', your_input)""")
    #regex_replacement_string = models.CharField(max_length=255, blank=True,\
    #        help_text='"[^0-9]"; Usage: re.sub("[^0-9]", "", "1234.99"')
    #python_code_snippet = models.TextField(blank=True, help_text='currently unused')
    #tranformation_function_name = models.CharField(max_length=255, blank=True, choices=TRANSFORMATION_FUNCTIONS)

    created = models.DateTimeField(auto_now_add=True)
    modified =models.DateTimeField(auto_now=True)

    def as_json(self):
        """Return the object in dict format"""
        info = dict(name=self.name,\
                description=self.description,\
                is_zero_padded=self.is_zero_padded,\
                expected_zero_padded_length=self.expected_zero_padded_length)
        if self.regex_match_string:
            info['regex_match_string'] = self.regex_match_string

        return info


    def __unicode__(self):
        return self.name



class JoinTarget(models.Model):
    """
    JoinTarget
    """
    name = models.CharField(max_length=100,\
        help_text='Will be presented to Geoconnect Users. e.g. "Boston Zip Codes (5 digit)"')
    layer = models.ForeignKey(Layer)
    attribute = models.ForeignKey(LayerAttribute)
    geocode_type = models.ForeignKey(GeocodeType, on_delete=models.PROTECT)
    expected_format = models.ForeignKey(JoinTargetFormatType, null=True, blank=True)
    year = models.IntegerField()

    created = models.DateTimeField(auto_now_add=True)
    modified =models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.layer.title

    class Meta:
        unique_together = ('layer', 'attribute',)
        ordering = ('year', 'name')

    def return_to_layer_admin(self):
        if not self.id or not self.layer:
            return 'n/a'
        layer_admin_link = reverse('admin:maps_layer_change', args=(self.layer.id,))
        return '<a href="%s">View Layer Admin</a>' % (layer_admin_link)
    return_to_layer_admin.allow_tags = True


    def as_json(self):
        """Return the object in dict format"""

        if self.expected_format:
            expected_format = self.expected_format.as_json()
        else:
            expected_format = None

        if self.layer.abstract:
            abstract = self.layer.abstract.strip()
        else:
            abstract = None

        return dict(id=self.id,\
            name=self.name,\
            layer=self.layer.typename,\
            title=self.layer.title,\
            abstract=abstract,\
            attribute={'attribute':self.attribute.attribute, 'type':self.attribute.attribute_type},\
            expected_format=expected_format,\
            geocode_type=self.geocode_type.name,\
            geocode_type_slug=self.geocode_type.slug,\
            year=self.year)


class LatLngTableMappingRecord(models.Model):
    datatable = models.ForeignKey(DataTable)

    lat_attribute = models.ForeignKey(DataTableAttribute, related_name="lat_attribute")
    lng_attribute = models.ForeignKey(DataTableAttribute, related_name="lng_attribute")

    layer = models.ForeignKey(Layer, related_name="mapped_layer", null=True, blank=True)

    mapped_record_count = models.IntegerField(default=0, help_text='Records mapped')
    unmapped_record_count = models.IntegerField(default=0, help_text='Records that failed to map Lat/Lng')
    unmapped_records_list = models.TextField(blank=True, help_text='Unmapped records')

    created = models.DateTimeField(auto_now_add=True)
    modified =models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s' % self.datatable

    def as_json(self):
        data_dict = {}

        straight_attrs = ('mapped_record_count', 'unmapped_record_count')#, 'created', 'modified')
        for attr in straight_attrs:
            data_dict[attr] = self.__dict__.get(attr)

        data_dict['lat_lng_record_id'] = self.id
        data_dict['datatable'] = self.datatable.table_name
        data_dict['datatable_id'] = self.datatable.id
        data_dict['layer_id'] = self.layer.id
        data_dict['layer_name'] = self.layer.name
        data_dict['layer_typename'] = self.layer.typename
        data_dict['layer_link'] = self.layer.get_absolute_url()

        data_dict['lat_attribute'] = dict(attribute=self.lat_attribute.attribute\
                    , type=self.lat_attribute.attribute_type)
        data_dict['lng_attribute'] = dict(attribute=self.lng_attribute.attribute\
                    , type=self.lng_attribute.attribute_type)
        if self.unmapped_records_list:
            try:
                data_dict['unmapped_records_list'] = json.loads(self.unmapped_records_list)
            except TypeError:
                data_dict['unmapped_records_list'] = self.unmapped_records_list

        return data_dict


    class Meta:
        verbose_name = 'Latitude/Longitude Table Mapping Record'

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
        drop_view_by_name(self.view_name)

    def as_json(self):
        return dict(
            id=self.id, datatable=self.datatable.table_name, source_layer=self.source_layer.typename, join_layer=self.join_layer.typename,
            join_layer_title=self.join_layer.title,
            table_attribute={'attribute':self.table_attribute.attribute, 'type':self.table_attribute.attribute_type},
            layer_attribute={'attribute':self.layer_attribute.attribute, 'type':self.layer_attribute.attribute_type},
            view_name=self.view_name,
            matched_records_count=self.matched_records_count,
            unmatched_records_count=self.unmatched_records_count,
            unmatched_records_list=self.unmatched_records_list)

# Used to generate Django form for JSON output and result evaluation
#  - a bit verbose, but easier to test with
#
TABLE_JOIN_TO_RESULT_MAP = dict(tablejoin_id='pk',
                             tablejoin_view_name='view_name',
                             join_layer_id='join_layer.id',
                             join_layer_typename='join_layer.typename',
                             join_layer_url='join_layer.get_absolute_url',
                             matched_record_count='matched_records_count',
                             unmatched_record_count='unmatched_records_count',
                             unmatched_records_list='unmatched_records_list',
                             table_id='datatable.id',
                             table_name='datatable.table_name',
                             table_join_attribute='table_attribute.attribute',
                             layer_typename='join_layer.typename',
                             layer_join_attribute='layer_attribute.attribute')

class TableJoinResult(models.Model):
    """
    Abstract model to return after a successful table join.

    """
    tablejoin_id = models.IntegerField(help_text='TableJoin pk')

    tablejoin_view_name = models.CharField(max_length=255, help_text='TableJoin view_name')

    # New Join Layer
    #
    join_layer_id = models.CharField(max_length=255\
                        , help_text='TableJoin join_layer.id')

    join_layer_typename = models.CharField(max_length=255\
                        , help_text='TableJoin join_layer.typename')

    join_layer_url = models.CharField(max_length=255\
                        , help_text='TableJoin join_layer.get_absolute_url()')


    matched_record_count = models.IntegerField(default=0, help_text='TableJoin matched_records_count')
    unmatched_record_count = models.IntegerField(default=0, help_text='TableJoin unmatched_records_count')
    unmatched_records_list = models.TextField(blank=True, help_text='TableJoin unmatched_records_list')

    table_id = models.IntegerField(help_text='TableJoin datatable.id')
    table_name = models.CharField(max_length=255, help_text='TableJoin datatable.table_name')
    table_join_attribute = models.CharField(max_length=255\
                        , help_text='TableJoin table_attribute.attribute')

    layer_typename = models.CharField(max_length=255, help_text='TableJoin join_layer.typename')
    layer_join_attribute = models.CharField(max_length=255\
                        , help_text='TableJoin layer_attribute.attribute')


    def __unicode__(self):
        return self.join_layer_typename

    class Meta:
        abstract = True



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
