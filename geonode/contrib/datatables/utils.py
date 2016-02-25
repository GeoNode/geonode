#from __future__ import print_function
import sys
import os
import uuid
import traceback
import logging
import string
from random import choice
from csvkit import sql
from csvkit import table

from geonode.contrib.msg_util import *

from geoserver.catalog import Catalog
from geoserver.store import datastore_from_index
from geoserver.resource import FeatureType

import psycopg2

from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from os.path import basename, splitext

from geonode.maps.models import Layer, LayerAttribute
from geonode.maps.gs_helpers import get_sld_for #fixup_style, cascading_delete, delete_from_postgis, get_postgis_bbox

from geonode.contrib.datatables.models import DataTable, DataTableAttribute, TableJoin
from geonode.contrib.datatables.forms import DataTableUploadForm, TableJoinRequestForm
from geonode.contrib.datatables.column_checker import ColumnChecker

from geonode.contrib.datatables.db_helper import get_datastore_connection_string

from shared_dataverse_information.shared_form_util.format_form_errors import format_errors_as_text
from .db_helper import CHOSEN_DB_SETTING

LOGGER = logging.getLogger(__name__)

THE_GEOM_LAYER_COLUMN = 'the_geom'
THE_GEOM_LAYER_COLUMN_REPLACEMENT = 'the_geom_col'


def standardize_name(col_name):
    """
    Format column names in tabular files
     - Special case for columns named "the_geom", replace them
    """
    assert col_name is not None, "col_name cannot be None"

    cname = slugify(unicode(col_name)).replace('-','_')
    if cname == THE_GEOM_LAYER_COLUMN:
        return THE_GEOM_LAYER_COLUMN_REPLACEMENT
    return cname


def standardize_table_name(tbl_name):
    assert tbl_name is not None, "tbl_name cannot be None"
    assert len(tbl_name) > 0, "tbl_name must be a least 1-char long, not zero"

    if tbl_name[:1].isdigit():
        tbl_name = 't-' + tbl_name

    return slugify(unicode(tbl_name)).replace('-','_')


def get_unique_tablename(table_name):
    """
    Check the database to see if a table_name already exists.
    If it does, generate a random extension and check again until an unused name is found.
    """
    assert table_name is not None, "table_name cannot be None"

    # ------------------------------------------------
    # slugify, change to unicode
    # ------------------------------------------------
    table_name = standardize_table_name(table_name)

    # ------------------------------------------------
    # Make 10 attempts to generate a unique table name
    # ------------------------------------------------
    unique_tname = table_name
    attempts = []
    for x in range(1, 11):
        attempts.append(unique_tname)   # save the attempt

        # Is this a unique name?  Yes, return it.
        if DataTable.objects.filter(table_name=unique_tname).count() == 0:
            return unique_tname

        # Not unique. Add 2 to 11 random chars to end of table_name
        #  attempts 1:-3 datatable_xx, datatable_xxx, datatable_xxxx where x is random char
        #
        random_chars = "".join([choice(string.ascii_lowercase + string.digits) for i in range(x+1)])
        unique_tname = '%s_%s' % (table_name, random_chars)
    # ------------------------------------------------
    # Failed to generate a unique name, throw an error
    # ------------------------------------------------
    err_msg = """Failed to generate unique table_name attribute for a new DataTable object.
Original: %s
Attempts: %s""" % (table_name, ', '.join(attempts))
    raise ValueError(err_msg)


def process_csv_file(data_table, delimiter=",", no_header_row=False):
    """
    Transform csv file and add it to the postgres DataStore

    :param instance:
    :param delimiter:
    :param no_header_row:
    :return:
        success:  (datatable, None)
        err:    (None, error message)
    """
    assert isinstance(data_table, DataTable), "instance must be a DataTable object"

    # full path to csv file
    #
    csv_filename = data_table.uploaded_file.path

    # Standardize table_name for the DataTable
    #
    if data_table.id is not None:
        # This DataTable already has a unique name
        table_name = data_table.table_name
    else:
        # Get a unique name for the data table
        table_name = os.path.splitext(os.path.basename(csv_filename))[0]
        table_name = get_unique_tablename(table_name)

        data_table.table_name = table_name
        data_table.save()

    # -----------------------------------------------------
    # Transform csv file to csvkit Table
    # -----------------------------------------------------
    f = open(csv_filename, 'rb')


    csv_table = table.Table.from_csv(f, name=table_name, no_header_row=no_header_row, delimiter=delimiter)
    try:
        pass
        #csv_table = table.Table.from_csv(f, name=table_name, no_header_row=no_header_row, delimiter=delimiter)
    except:
        data_table.delete()
        err_msg = str(sys.exc_info()[0])
        LOGGER.error('Failed to convert csv file to table.  Error: %s' % err_msg)
        return None, err_msg
    #csv_file = File(f)
    f.close()

    # -----------------------------------------------------
    # Create DataTableAttribute objects
    # -----------------------------------------------------
    try:
        # Iterate through header row
        #
        for column in csv_table:

            # Standardize column name
            #
            column.name = standardize_name(column.name)

            # Create DataTableAttribute object
            #
            is_visible = True
            if column.name == '_unnamed':
                is_visible = False

            attribute, created = DataTableAttribute.objects.get_or_create(datatable=data_table,
                    attribute=column.name,
                    attribute_label=column.name,
                    attribute_type=column.type.__name__,
                    display_order=column.order,
                    visible=is_visible)
    except:
        data_table.delete()     # Deleting DataTable also deletes related DataTableAttribute objects
        err_msg = 'Failed to convert csv file to table.  Error: %s' % str(sys.exc_info()[0])
        LOGGER.error(err_msg)
        return None, err_msg


    msg('process_csv_file 3')
    # -----------------------------------------------------
    # Generate SQL to create table from csv file
    # -----------------------------------------------------
    try:
        sql_table = sql.make_table(csv_table,table_name)
        create_table_sql = sql.make_create_table_statement(sql_table, dialect="postgresql")
        data_table.create_table_sql = create_table_sql
        data_table.save()
    except:
        data_table.delete()
        err_msg = 'Generate SQL to create table from csv file.  Error: %s' % str(sys.exc_info()[0])
        LOGGER.error(err_msg)
        return None, err_msg

    msg('process_csv_file 4')

    # -----------------------------------------------------
    # Execute the SQL and Create the Table (No data is loaded)
    # -----------------------------------------------------
    conn = psycopg2.connect(get_datastore_connection_string())

    try:
        cur = conn.cursor()
        cur.execute('drop table if exists %s CASCADE;' % table_name)
        cur.execute(create_table_sql)
        conn.commit()
    except Exception as e:
        traceback.print_exc(sys.exc_info())
        err_msg =  "Error Creating table %s:%s" % (data_table.name, str(e))
        LOGGER.error(err_msg)
        return None, err_msg

    finally:
        conn.close()

    # -----------------------------------------------------
    # Copy Data to postgres csv data to Postgres
    # -----------------------------------------------------
    #connection_string = "postgresql://%s:%s@%s:%s/%s" % (db['USER'], db['PASSWORD'], db['HOST'], db['PORT'], db['NAME'])

    connection_string = get_datastore_connection_string(url_format=True)
    try:
        engine, metadata = sql.get_connection(connection_string)
    except ImportError:
        err_msg =  "Failed to get SQL connection for copying csv data to database.\n%s" % str(sys.exc_info()[0])
        LOGGER.error(err_msg)
        return None, err_msg


    # -----------------------------------------------------
    # Iterate through rows and add data
    # -----------------------------------------------------
    conn = engine.connect()
    trans = conn.begin()

    if csv_table.count_rows() > 0:
        insert = sql_table.insert()     # Generate insert statement
        headers = csv_table.headers()   # Pull table headers
        try:
            # create rows of { column : value } dict's
            #
            rows_to_add = [dict(zip(headers, row)) for row in csv_table.to_rows()]

            # Add rows
            conn.execute(insert, rows_to_add)
        except:
            # Clean up after ourselves
            instance.delete()
            err_msg =  "Failed to add csv DATA to table %s.\n%s" % (table_name, (sys.exc_info()[0]))
            LOGGER.error(err_msg)
            return None, err_msg


    # Commit new rows and close connection
    #
    trans.commit()
    conn.close()
    f.close()

    return data_table, ""


def setup_join(new_table_owner, table_name, layer_typename, table_attribute_name, layer_attribute_name):
    LOGGER.info('setup_join')
    """
    Setup the Table Join in GeoNode
    """
    assert isinstance(new_table_owner, User), "new_table_owner must be a User object"
    assert table_name is not None, "table_name cannot be None"
    assert layer_typename is not None, "layer_typename cannot be None"
    assert table_attribute_name is not None, "table_attribute_name cannot be None"
    assert layer_attribute_name is not None, "layer_attribute_name cannot be None"

    LOGGER.info('setup_join. Step (1): Retrieve the DataTable object')
    try:
        dt = DataTable.objects.get(table_name=table_name)
    except DataTable.DoesNotExist:
        err_msg = 'No DataTable object found for table_name "%s"' % table_name
        LOGGER.error(err_msg)
        return None, err_msg

    LOGGER.info('setup_join. Step (2): Retrieve the Layer object')

    try:
        layer = Layer.objects.get(typename=layer_typename)
    except Layer.DoesNotExist:
        err_msg = 'No Layer object found for layer_typename "%s"' % layer_typename
        LOGGER.error(err_msg)
        return None, err_msg

    LOGGER.info('setup_join. Step (3): Retrieve the DataTableAttribute object')
    try:
        table_attribute = DataTableAttribute.objects.get(datatable=dt,attribute=table_attribute_name)
    except DataTableAttribute.DoesNotExist:
        err_msg = 'No DataTableAttribute object found for table/attribute (%s/%s)' \
                  % (dt, table_attribute_name)
        LOGGER.error(err_msg)
        return None, err_msg

    LOGGER.info('setup_join. Step (4): Retrieve the LayerAttribute object')
    try:
        layer_attribute = LayerAttribute.objects.get(layer=layer, attribute=layer_attribute_name)
    except LayerAttribute.DoesNotExist:
        err_msg = 'No LayerAttribute object found for layer/attribute (%s/%s)' \
                  % (layer, layer_attribute_name)
        LOGGER.error(err_msg)
        return None, err_msg

    LOGGER.info('setup_join. Step (5): Build SQL statement to create view')

    layer_name = layer.typename.split(':')[1]

    view_name = "join_%s_%s" % (layer_name, dt.table_name)

    view_sql = 'create view %s as select %s.%s, %s.* from %s inner join %s on %s."%s" = %s."%s";' %  (view_name, layer_name, THE_GEOM_LAYER_COLUMN, dt.table_name, layer_name, dt.table_name, layer_name, layer_attribute.attribute, dt.table_name, table_attribute.attribute)
    #view_sql = 'create materialized view %s as select %s.the_geom, %s.* from %s inner join %s on %s."%s" = %s."%s";' %  (view_name, layer_name, dt.table_name, layer_name, dt.table_name, layer_name, layer_attribute.attribute, dt.table_name, table_attribute.attribute)

    # ------------------------------------------------------------------
    # (5a) Check if the join columns compatible
    # ------------------------------------------------------------------
    column_checker = ColumnChecker(layer_name, layer_attribute.attribute,
                            dt.table_name, table_attribute.attribute)
    (are_cols_compatible, user_err_msg) = column_checker.are_join_columns_compatible()
    if not are_cols_compatible:     # Doesn't look good, return an error message
        return None, user_err_msg


    #double_view_name = "view_%s" % view_name
    #double_view_sql = "create view %s as select * from %s" % (double_view_name, view_name)
    LOGGER.info('setup_join. Step (6): Retrieve stats')

    # ------------------------------------------------------------------
    # Retrieve stats
    # ------------------------------------------------------------------
    matched_count_sql = 'select count(%s) from %s where %s.%s in (select "%s" from %s);'\
                        % (table_attribute.attribute, dt.table_name, dt.table_name, table_attribute.attribute, layer_attribute.attribute, layer_name)

    unmatched_count_sql = 'select count(%s) from %s where %s.%s not in (select "%s" from %s);'\
                        % (table_attribute.attribute, dt.table_name, dt.table_name, table_attribute.attribute, layer_attribute.attribute, layer_name)

    unmatched_list_sql = 'select %s from %s where %s.%s not in (select "%s" from %s) limit 100;'\
                        % (table_attribute.attribute, dt.table_name, dt.table_name, table_attribute.attribute, layer_attribute.attribute, layer_name)

    # ------------------------------------------------------------------
    # Create a TableJoin object
    # ------------------------------------------------------------------
    LOGGER.info('setup_join. Step (7): Create a TableJoin object')
    tj, created = TableJoin.objects.get_or_create(source_layer=layer
                            , datatable=dt
                            , table_attribute=table_attribute
                            , layer_attribute=layer_attribute
                            , view_name=view_name
                            , view_sql=view_sql)
    tj.save()
    msgt('table join created! %s' % tj.id )

    # ------------------------------------------------------------------
    # Create the View (and double view)
    # ------------------------------------------------------------------
    LOGGER.info('setup_join. Step (8): Create the View (and double view)')
    try:
        conn = psycopg2.connect(get_datastore_connection_string())

        cur = conn.cursor()
        #cur.execute('drop view if exists %s;' % double_view_name)  # removing double view
        cur.execute('drop view if exists %s;' % view_name)
        #cur.execute('drop materialized view if exists %s;' % view_name)
        msg('view_sql: %s'% view_sql)
        cur.execute(view_sql)
        #cur.execute(double_view_sql)
        cur.execute(matched_count_sql)
        tj.matched_records_count = cur.fetchone()[0]
        cur.execute(unmatched_count_sql)
        tj.unmatched_records_count = int(cur.fetchone()[0])
        cur.execute(unmatched_list_sql)
        tj.unmatched_records_list = ",".join([r[0] for r in cur.fetchall()])
        conn.commit()
        conn.close()

        # If no records match, then delete the TableJoin
        #
        if tj.matched_records_count == 0:
            # Delete the table join
            tj.delete()

            # Create an error message, log it, and send it back
            err_msg = 'Sorry!  No records matched.  Make sure that you chose the correct column and that the chosen layer is in the same geographic area.'
            LOGGER.error(err_msg)
            return None, err_msg

    except Exception as e:
        if conn:
            conn.close()

        tj.delete() # If needed for debugging, don't delete the table join
        traceback.print_exc(sys.exc_info())
        err_msg =  "Error Joining table %s to layer %s: %s" % (table_name, layer_typename, str(e[0]))
        LOGGER.error(err_msg)
        if err_msg.find('You might need to add explicit type casts.') > -1:
            user_msg = "The chosen column is a different data type than the one expected."
        else:
            user_msg = err_msg
        return None, user_msg


    #--------------------------------------------------
    # Create the Layer in GeoServer from the view
    #--------------------------------------------------
    LOGGER.info('setup_join. Step (9): Create the Layer in GeoServer from the view')
    try:
        LOGGER.info('setup_join. Step (9a): Find the datastore')
        #----------------------------
        # Find the datastore
        #----------------------------
        cat = Catalog(settings.GEOSERVER_BASE_URL + "rest",
                    settings.GEOSERVER_CREDENTIALS[0],
                    settings.GEOSERVER_CREDENTIALS[1])
                    # "admin", "geoserver")
        workspace = cat.get_workspace('geonode')
        ds_list = cat.get_xml(workspace.datastore_url)
        datastores = [datastore_from_index(cat, workspace, n) for n in ds_list.findall("dataStore")]
        ds = None

        # Iterate through datastores
        #
        for datastore in datastores:
            #msg ('datastore name:', datastore.name)
            if datastore.name == settings.DB_DATASTORE_NAME: #"geonode_imports":
                ds = datastore

        if ds is None:
            tj.delete()
            err_msg = "Datastore name not found: %s" % settings.DB_DATASTORE_NAME
            LOGGER.error(str(ds))
            return None, err_msg

        # Publish the feature
        #
        LOGGER.info('setup_join. Step (9b): Publish the feature type')
        ft = cat.publish_featuretype(view_name, ds, layer.srs, srs=layer.srs)
        #ft = cat.publish_featuretype(double_view_name, ds, layer.srs, srs=layer.srs)

        LOGGER.info('setup_join. Step (9c): Save the feature type')
        cat.save(ft)

    except Exception as e:
        tj.delete()
        traceback.print_exc(sys.exc_info())
        err_msg = "Error creating GeoServer layer for %s: %s" % (view_name, str(e))
        LOGGER.error(err_msg)
        return None, err_msg


    # ------------------------------------------------------
    # Set the Layer's default Style
    # ------------------------------------------------------
    set_default_style_for_new_layer(cat, ft)

    # ------------------------------------------------------------------
    # Create the Layer in GeoNode from the GeoServer Layer
    # ------------------------------------------------------------------
    LOGGER.info('setup_join. Step (10): Create the Layer in GeoNode from the GeoServer Layer')
    try:
        layer_params = {
            "workspace": workspace.name,
            "store": ds.name,
            "storeType": ds.resource_type,
            "typename": "%s:%s" % (workspace.name.encode('utf-8'), ft.name.encode('utf-8')),
            "title": ft.title or 'No title provided',
            "abstract": ft.abstract or 'No abstract provided',
            "uuid": str(uuid.uuid4()),
            "owner" : new_table_owner,
            #"bbox_x0": Decimal(ft.latlon_bbox[0]),
            #"bbox_x1": Decimal(ft.latlon_bbox[1]),
            #"bbox_y0": Decimal(ft.latlon_bbox[2]),
            #"bbox_y1": Decimal(ft.latlon_bbox[3])
        }

        layer, created = Layer.objects.get_or_create(name=view_name, defaults=layer_params)

        # Set default permissions (public)
        layer.set_default_permissions()
        #set_attributes(layer, overwrite=True)

        tj.join_layer = layer
        tj.save()
    except Exception as e:
        tj.delete()
        traceback.print_exc(sys.exc_info())
        err_msg = "Error creating GeoNode layer for %s: %s" % (view_name, str(e))
        LOGGER.error(err_msg)
        return None, err_msg

    # ------------------------------------------------------------------
    # Create LayerAttributes for the new Layer (not done in GeoNode 2.x)
    # ------------------------------------------------------------------
    LOGGER.info('setup_join. Step (11): Create Layer Attributes from the Datatable')
    (attributes_created, err_msg) = create_layer_attributes_from_datatable(dt, layer)
    if not attributes_created:
        LOGGER.error(err_msg)
        tj.delete() # Delete the table join object
        return None, "Sorry there was an error creating the Datatable (s11)"

    return tj, ""


def set_default_style_for_new_layer(geoserver_catalog, feature_type):
    """
    For a newly created Geoserver layer in the Catalog, set a default style

    :param catalog:
    :param feature_type:

    Returns success (True,False), err_msg (if False)
    """
    assert isinstance(geoserver_catalog, Catalog)
    assert isinstance(feature_type, FeatureType)

    # ----------------------------------------------------
    # Retrieve the layer from the catalog
    # ----------------------------------------------------
    new_layer = geoserver_catalog.get_layer(feature_type.name)

    # ----------------------------------------------------
    # Retrieve the SLD for this layer
    # ----------------------------------------------------
    sld = get_sld_for(new_layer)
    #msgt('SLD retrieved: %s' % sld)

    if sld is None:
        err_msg = 'Failed to retrieve the SLD for the geoserver layer: %s' % feature_type.name
        LOGGER.error(err_msg)
        return False, err_msg

    # ----------------------------------------------------
    # Create a new style name
    # ----------------------------------------------------
    random_ext = "".join([choice(string.ascii_lowercase + string.digits) for i in range(4)])
    new_layer_stylename = '%s_%s' % (feature_type.name, random_ext)

    msg('new_layer_stylename: %s' % new_layer_stylename)

    # ----------------------------------------------------
    # Add this new style to the catalog
    # ----------------------------------------------------
    try:
        geoserver_catalog.create_style(new_layer_stylename, sld)
        msg('created!')
    except geoserver.catalog.ConflictingDataError, e:
        err_msg = (_('There is already a style in GeoServer named ') +
                        '"%s"' % (name))
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
    return True


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


def attempt_datatable_upload_from_request_params(request, new_layer_owner):
    """
    Using request parameters, attempt a TableJoin

    Error:  (False, Error Message)
    Success: (True, TableJoin object)
    """
    LOGGER.info('contrib.datatables.utils.attempt_tablejoin_from_request_params')
    if not isinstance(new_layer_owner, User):
        return (False, "Please specify an owner for the new layer.")


    # ----------------------------------
    # Is this a POST?
    # ----------------------------------
    if not request.method == 'POST':
        err_msg = "Unsupported Method"
        return (False, err_msg)

    LOGGER.info('Step (a): Verify Request')

    # ---------------------------------------
    # Verify Request
    # ---------------------------------------
    form = DataTableUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        err_msg = "Form errors found. %s" % format_errors_as_text(form)#.as_json()#.as_text()
        return (False, err_msg)

    LOGGER.info('Step (b): Prepare data, create DataTable object')

    data = form.cleaned_data

    table_name = get_unique_tablename(splitext(basename(request.FILES['uploaded_file'].name))[0])

    instance = DataTable(uploaded_file=request.FILES['uploaded_file'],
                         table_name=table_name,
                         tablespace=CHOSEN_DB_SETTING,
                         title=data['title'],
                         abstract=data['abstract'],
                         delimiter=data['delimiter'],
                         owner=request.user)
    delimiter = data['delimiter']
    no_header_row = data['no_header_row']

    # save DataTable object
    instance.save()

    LOGGER.info('Step (d): Process the tabular file')

    (new_datatable_obj, result_msg) = process_csv_file(instance, delimiter=delimiter, no_header_row=no_header_row)

    if new_datatable_obj:
        LOGGER.info('Step (d1): Success!')

        # -----------------------------------------
        #  Success, DataTable created
        # -----------------------------------------
        return (True, new_datatable_obj)
    else:
        LOGGER.info('Step (d2): Failed!')
        # -----------------------------------------
        #  Failed, DataTable not created
        # -----------------------------------------
        return (False, result_msg)


def attempt_tablejoin_from_request_params(table_join_params, new_layer_owner):
    """
    Using request parameters, attempt a TableJoin

    Error:  (False, Error Message)
    Success: (True, TableJoin object)
    """
    LOGGER.info('attempt_tablejoin_from_request_params')
    if not isinstance(new_layer_owner, User):
        return (False, "Please specify an owner for the new layer.")


    LOGGER.info('Step (a): Validate the request params')

    # ----------------------------------
    # Validate the request params
    # ----------------------------------
    f = TableJoinRequestForm(table_join_params)
    if not f.is_valid():
        err_msg = "Form errors found. %s" % format_errors_as_text(f)
        return (False, err_msg)

    # DataTable and join attribute
    table_name = f.cleaned_data['table_name']
    table_attribute = f.cleaned_data['table_attribute']

    # Layer and join attribute
    layer_typename = f.cleaned_data['layer_name']
    layer_attribute = f.cleaned_data['layer_attribute']


    # ----------------------------------
    # Attempt to Join the table to an existing layer
    # ----------------------------------
    LOGGER.info('Step (b): Attempt to Join the table to an existing layer')

    try:
        table_join_obj, result_msg = setup_join(new_layer_owner, table_name, layer_typename, table_attribute, layer_attribute)
        if table_join_obj:
            LOGGER.info('Step (b1): Success')
            # Successful Join
            return (True, table_join_obj)
        else:
            LOGGER.info('Step (b2): Failure', result_msg)
            # Error!
            err_msg = "Error Creating Join: %s" % result_msg
            return (False, err_msg)
    except:
        traceback.print_exc(sys.exc_info())
        err_msg = "Error Creating Join: %s" % str(sys.exc_info()[0])
        return (False, err_msg)
