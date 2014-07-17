from __future__ import unicode_literals

import keyword
import re

from django.utils.datastructures import SortedDict
from django.conf import settings
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.db import models
from django.contrib.gis import admin
from django.core.exceptions import ValidationError
from django import db

from geonode.layers.models import Layer

from .postgis import file2pgtable

DYNAMIC_DATASTORE = 'datastore'


class ModelDescription(models.Model):
    name = models.CharField(max_length=255)
    layer = models.ForeignKey(Layer, null=True, blank=True)

    def get_django_model(self, with_admin=False):
        "Returns a functional Django model based on current data"
        # Get all associated fields into a list ready for dict()
        fields = [(f.name, f.get_django_field()) for f in self.fields.all()]

        # Use the create_model function defined above
        return create_model(self.name, dict(fields),
                            app_label='dynamic',
                            module='geonode.contrib.dynamic',
                            options={'db_table': self.name,
                                     'managed': False
                                     },
                            with_admin=with_admin,
                            )

    def data_objects(self):
        """
        """
        TheModel = self.get_django_model()
        return TheModel.using(DYNAMIC_DATASTORE)


def is_valid_field(self, field_data, all_data):
    if hasattr(
            models,
            field_data) and issubclass(
            getattr(
                models,
                field_data),
            models.Field):
        # It exists and is a proper field type
        return
    raise ValidationError("This is not a valid field type.")


class Field(models.Model):
    model = models.ForeignKey(ModelDescription, related_name='fields')
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, validators=[is_valid_field])
    original_name = models.CharField(max_length=255)

    def get_django_field(self):
        "Returns the correct field type, instantiated with applicable settings"
        # Get all associated settings into a list ready for dict()
        settings = [(s.name, s.value) for s in self.settings.all()]  # noqa

        field_type = getattr(models, self.type)

        # Instantiate the field with the settings as **kwargs
        return field_type(**dict(settings))

    class Meta:
        unique_together = (('model', 'name'),)


class Setting(models.Model):
    field = models.ForeignKey(Field, related_name='settings')
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = (('field', 'name'),)


def create_model(
        name,
        fields=None,
        app_label='',
        module='',
        options=None,
        admin_opts=None,
        with_admin=False):
    """
    Create specified model
    """
    class Meta:
        # Using type('Meta', ...) gives a dictproxy error during model creation
        pass

    if app_label:
        # app_label must be set using the Meta inner class
        setattr(Meta, 'app_label', app_label)

    # Update Meta with any options that were provided
    if options is not None:
        for key, value in options.iteritems():
            setattr(Meta, key, value)

    # Set up a dictionary to simulate declarations within a class
    attrs = {'__module__': module, 'Meta': Meta}

    # Add in any fields that were provided
    if fields:
        attrs.update(fields)

    # Create the class, which automatically triggers ModelBase processing
    model = type(str(name), (models.Model,), attrs)

    class Admin(admin.OSMGeoAdmin):

        """Takes into account multi-db queries.
        """
        using = DYNAMIC_DATASTORE

        def save_model(self, request, obj, form, change):
            # Tell Django to save objects to the 'other' database.
            obj.save(using=self.using)

        def delete_model(self, request, obj):
            # Tell Django to delete objects from the 'other' database
            obj.delete(using=self.using)

        def get_queryset(self, request):
            # Tell Django to look for objects on the 'other' database.
            return super(Admin, self).get_queryset(request).using(self.using)

        def queryset(self, request):
            # Tell Django to look for objects on the 'other' database.
            return super(Admin, self).queryset(request).using(self.using)

        def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
            # Tell Django to populate ForeignKey widgets using a query
            # on the 'other' database.
            return super(
                Admin,
                self).formfield_for_foreignkey(
                db_field,
                request=request,
                using=self.using,
                **kwargs)

        def formfield_for_manytomany(self, db_field, request=None, **kwargs):
            # Tell Django to populate ManyToMany widgets using a query
            # on the 'other' database.
            return super(
                Admin,
                self).formfield_for_manytomany(
                db_field,
                request=request,
                using=self.using,
                **kwargs)

    # Create an Admin class if admin options were provided
    if admin_opts is not None:

        for key, value in admin_opts:
            setattr(Admin, key, value)

    if not with_admin:
        return model
    else:
        return model, Admin


def generate_model(model_description, mapping, db_key=''):
    """Uses instrospection to generate a Django model from a database table.
    """
    connection = db.connections[db_key]
    cursor = connection.cursor()

    table_name = model_description.name

    try:
        relations = connection.introspection.get_relations(cursor, table_name)
    except NotImplementedError:
        relations = {}
    try:
        indexes = connection.introspection.get_indexes(cursor, table_name)
    except NotImplementedError:
        indexes = {}
    used_column_names = []  # Holds column names used in the table so far
    for i, row in enumerate(connection.introspection.get_table_description(cursor, table_name)):
        # Holds Field notes, to be displayed in a Python comment.
        comment_notes = []
        # Holds Field parameters such as 'db_column'.
        extra_params = SortedDict()
        column_name = row[0]
        is_relation = i in relations

        att_name, params, notes = normalize_col_name(
            column_name,
            used_column_names,
            is_relation
        )
        extra_params.update(params)
        comment_notes.extend(notes)

        used_column_names.append(att_name)

        # Add primary_key and unique, if necessary.
        if column_name in indexes:
            if indexes[column_name]['primary_key']:
                extra_params['primary_key'] = True
            elif indexes[column_name]['unique']:
                extra_params['unique'] = True

        # Calling `get_field_type` to get the field type string and any
        # additional parameters and notes
        field_type, field_params, field_notes = get_field_type(
            connection, table_name, row)
        extra_params.update(field_params)
        comment_notes.extend(field_notes)

        GEOM_FIELDS = {
            'GEOMETRYCOLLECTION': 'GeometryCollectionField',
            'POINT': 'PointField',
            'MULTIPOINT': 'MultiPointField',
            'LINESTRING': 'LineStringField',
            'MULTILINESTRING': 'MultiLineStringField',
            'POLYGON': 'PolygonField',
            'MULTIPOLYGON': 'MultiPolygonField',
            'GEOMETRY': 'GeometryField',
        }

        geom_type = mapping['geom']

        # Use the geom_type to override the geometry field.
        if field_type == 'GeometryField':
            if geom_type in GEOM_FIELDS:
                field_type = GEOM_FIELDS[geom_type]

        # Change the type of id to AutoField to get auto generated ids.
        if att_name == 'id' and extra_params == {'primary_key': True}:
            field_type = 'AutoField'

        # Add 'null' and 'blank', if the 'null_ok' flag was present in the
        # table description.
        if row[6]:  # If it's NULL...
            if field_type == 'BooleanField':
                field_type = 'NullBooleanField'
            else:
                extra_params['blank'] = True
                if field_type not in ('TextField', 'CharField'):
                    extra_params['null'] = True

        if any(field_type) and column_name != 'id':
            field, __ = Field.objects.get_or_create(
                model=model_description, name=att_name)
            field.type = field_type
            field.original_name = mapping[column_name]

            field.save()

            for name, value in extra_params.items():
                if any(name):
                    Setting.objects.get_or_create(
                        field=field,
                        name=name,
                        value=value)


def normalize_col_name(col_name, used_column_names, is_relation):
    """
    Modify the column name to make it Python-compatible as a field name
    """
    field_params = {}
    field_notes = []

    new_name = col_name.lower()
    if new_name != col_name:
        field_notes.append('Field name made lowercase.')

    if is_relation:
        if new_name.endswith('_id'):
            new_name = new_name[:-3]
        else:
            field_params['db_column'] = col_name

    new_name, num_repl = re.subn(r'\W', '_', new_name)
    if num_repl > 0:
        field_notes.append('Field renamed to remove unsuitable characters.')

    if new_name.find('__') >= 0:
        while new_name.find('__') >= 0:
            new_name = new_name.replace('__', '_')
        if col_name.lower().find('__') >= 0:
            # Only add the comment if the double underscore was in the original
            # name
            field_notes.append(
                "Field renamed because it contained more than one '_' in a row.")

    if new_name.startswith('_'):
        new_name = 'field%s' % new_name
        field_notes.append("Field renamed because it started with '_'.")

    if new_name.endswith('_'):
        new_name = '%sfield' % new_name
        field_notes.append("Field renamed because it ended with '_'.")

    if keyword.iskeyword(new_name):
        new_name += '_field'
        field_notes.append(
            'Field renamed because it was a Python reserved word.')

    if new_name[0].isdigit():
        new_name = 'number_%s' % new_name
        field_notes.append(
            "Field renamed because it wasn't a valid Python identifier.")

    if new_name in used_column_names:
        num = 0
        while '%s_%d' % (new_name, num) in used_column_names:
            num += 1
        new_name = '%s_%d' % (new_name, num)
        field_notes.append('Field renamed because of name conflict.')

    if col_name != new_name and field_notes:
        field_params['db_column'] = col_name

    return new_name, field_params, field_notes


def get_field_type(connection, table_name, row):
    """
    Given the database connection, the table name, and the cursor row
    description, this routine will return the given field type name, as
    well as any additional keyword parameters and notes for the field.
    """
    field_params = SortedDict()
    field_notes = []

    try:
        field_type = connection.introspection.get_field_type(row[1], row)
    except KeyError:
        field_type = 'TextField'
        field_notes.append('This field type is a guess.')

    # This is a hook for DATA_TYPES_REVERSE to return a tuple of
    # (field_type, field_params_dict).
    if isinstance(field_type, tuple):
        field_type, new_params = field_type
        field_params.update(new_params)

    # Add max_length for all CharFields.
    if field_type == 'CharField' and row[3]:
        field_params['max_length'] = int(row[3])

    if field_type == 'DecimalField':
        field_params['max_digits'] = row[4]
        field_params['decimal_places'] = row[5]

    return field_type, field_params, field_notes


def pre_save_layer(instance, sender, **kwargs):
    """Save to postgis if there is a datastore.
    """
    # Abort if a postgis DATABASE is not configured.
    if DYNAMIC_DATASTORE not in settings.DATABASES:
        return

    # Do not process if there is no table.
    base_file = instance.get_base_file()
    if base_file is None or base_file.name != 'shp':
        return

    filename = base_file.file.path

    # Load the table in postgis and get a mapping from fields in the database
    # and fields in the Shapefile.
    mapping = file2pgtable(filename, instance.name)

    # Get a dynamic model with the same name as the layer.
    model_description, __ = ModelDescription.objects.get_or_create(
        name=instance.name)

    # Set up the fields with the postgis table
    generate_model(model_description, mapping, db_key=DYNAMIC_DATASTORE)

    # Get the new actual Django model.
    TheModel = model_description.get_django_model()

    # Use layermapping to load the layer with geodjango
    lm = LayerMapping(TheModel, filename, mapping,
                      encoding=instance.charset,
                      using=DYNAMIC_DATASTORE,
                      transform=None
                      )
    lm.save()


def post_save_layer(instance, sender, **kwargs):
    """Assign layer instance to the dynamic model.
    """
    # Assign this layer model to all ModelDescriptions with the same name.
    ModelDescription.objects.filter(name=instance.name).update(layer=instance)


models.signals.pre_save.connect(pre_save_layer, sender=Layer)
models.signals.post_save.connect(post_save_layer, sender=Layer)
