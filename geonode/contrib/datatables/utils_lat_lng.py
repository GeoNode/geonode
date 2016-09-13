"""
Functions for creating maps from tabular files with lat/lng columns.
Incudes creation of DataTable, Layer, and LatLngTableMappingRecord objects
"""
import datetime
import json
import sys
import traceback
import uuid

# Postgres
import psycopg2
from geonode.contrib.datatables.db_helper import get_datastore_connection_string

from django.conf import settings
from django.contrib.auth.models import User

from geoserver.catalog import Catalog
from geoserver.store import datastore_from_index

from geonode.maps.models import Layer
from geonode.contrib.datatables.models import DataTable, DataTableAttribute,\
    LatLngTableMappingRecord

#from geonode.contrib.datatables.utils import set_default_style_for_latlng_layer,\
#    create_layer_attributes_from_datatable
from geonode.contrib.datatables.layer_helper import set_default_style_for_latlng_layer,\
    create_layer_attributes_from_datatable
from geonode.contrib.datatables.name_helper import standardize_column_name

from geonode.contrib.msg_util import *

import logging
LOGGER = logging.getLogger(__name__)


def is_valid_lat_lng_attribute(dt_attr, lng_check=False):
    """
    success: return True, None
    fail: return False, err_msg
    """
    assert isinstance(dt_attr, DataTableAttribute)

    if dt_attr.attribute_type.find('float') > -1:
        return True, None

    if dt_attr.attribute_type.find('double') > -1:
        return True, None

    col_type = 'latitude'
    if lng_check:
        col_type = 'longitude'

    err_msg = 'Not a valid %s column. Column "%s" is type "%s".   All data in the column must be a float or double.' \
                                    % (col_type, dt_attr.attribute, dt_attr.attribute_type)
    return False, err_msg


def create_point_col_from_lat_lon(new_table_owner, table_name, lat_column, lng_column):
    """
    Using a new DataTable and specified lat/lng column names, map the points

    :param new_table_owner:
    :param table_name:
    :param lat_column:
    :param lng_column:
    :return:
    """

    LOGGER.info('create_point_col_from_lat_lon')
    assert isinstance(new_table_owner, User), "new_table_owner must be a User object"
    assert table_name is not None, "table_name cannot be None"
    assert lat_column is not None, "lat_column cannot be None"
    assert lng_column is not None, "lng_column cannot be None"

    # ----------------------------------------------------
    # Retrieve the DataTable and check for lat/lng columns
    # ----------------------------------------------------
    try:
        dt = DataTable.objects.get(table_name=table_name)
    except DataTable.DoesNotExist:
        err_msg = "Could not find DataTable with name: %s" % (table_name)
        LOGGER.error(err_msg)
        return False, err_msg

    # ----------------------------------------------------
    # Latitude attribute
    # ----------------------------------------------------
    lat_col_attr = dt.get_attribute_by_name(standardize_column_name(lat_column))
    if lat_col_attr is None:
        err_msg = 'DataTable "%s" does not have a latitude column named "%s" (formatted: %s)'\
                  % (table_name, lat_column, standardize_column_name(lat_column))
        LOGGER.error(err_msg)
        return False, err_msg

    is_valid, err_msg = is_valid_lat_lng_attribute(lat_col_attr)
    if not is_valid:
        LOGGER.error(err_msg)
        return False, err_msg


    # ----------------------------------------------------
    # Longitude attribute
    # ----------------------------------------------------
    lng_col_attr = dt.get_attribute_by_name(standardize_column_name(lng_column))
    if lng_col_attr is None:
        err_msg = 'DataTable "%s" does not have a longitude column named "%s" (formatted: %s)'\
                  % (table_name, lng_column, standardize_column_name(lng_column))
        LOGGER.error(err_msg)
        return False, err_msg

    is_valid, err_msg = is_valid_lat_lng_attribute(lng_col_attr, lng_check=True)
    if not is_valid:
        LOGGER.error(err_msg)
        return False, err_msg

    # ----------------------------------------------------
    # Start mapping record
    # ----------------------------------------------------
    lat_lnt_map_record = LatLngTableMappingRecord(datatable=dt\
                                , lat_attribute=lat_col_attr\
                                , lng_attribute=lng_col_attr\
                                )

    msg('create_point_col_from_lat_lon - 2')

    # ----------------------------------------------------
    # Yank bad columns out of the DataTable
    # ----------------------------------------------------
    # See https://github.com/IQSS/dataverse/issues/2949

    (success, row_cnt_or_err_msg) = remove_bad_lat_lng_numbers(lat_lnt_map_record)
    if not success:
        if lat_lnt_map_record.id:
            lat_lnt_map_record.delete()
        return False, 'Failed to remove bad lat/lng values.'

    # The bad rows were not mapped
    lat_lnt_map_record.unmapped_record_count = row_cnt_or_err_msg

    # ---------------------------------------------
    # Format SQL to:
    #   (a) Add the Geometry column to the Datatable
    #   (b) Populate the column using the lat/lng attributes
    #   (c) Create column index
    # ---------------------------------------------
    # (a) Add column SQL
    alter_table_sql = "ALTER TABLE %s ADD COLUMN geom geometry;" % (table_name) # postgis 1.x
    #alter_table_sql = "ALTER TABLE %s ADD COLUMN geom geometry(POINT,4326);" % (table_name) # postgi 2.x

    # (b) Populate column SQL
    update_table_sql = "UPDATE %s SET geom = ST_SetSRID(ST_MakePoint(%s,%s),4326);" \
                    % (table_name, lng_col_attr.attribute, lat_col_attr.attribute)
    #update_table_sql = "UPDATE %s SET geom = ST_SetSRID(ST_MakePoint(cast(%s AS float), cast(%s as float)),4326);" % (table_name, lng_column, lat_column)
    msg('update_table_sql: %s' % update_table_sql)

    # (c) Index column SQL
    create_index_sql = "CREATE INDEX idx_%s_geom ON %s USING GIST(geom);" % (table_name, table_name)

    msg('create_point_col_from_lat_lon - 3')

    # ---------------------------------------------
    # Run the SQL
    # ---------------------------------------------
    try:
        conn = psycopg2.connect(get_datastore_connection_string(is_dataverse_db=False))

        cur = conn.cursor()

        cur.execute(alter_table_sql)
        cur.execute(update_table_sql)
        cur.execute(create_index_sql)
        conn.commit()
        conn.close()
    except Exception as e:
        conn.close()
        err_msg =  "Error Creating Point Column from Latitude and Longitude %s" % (str(e[0]))
        LOGGER.error(err_msg)
        return False, err_msg

    msg('create_point_col_from_lat_lon - 4')

    # ------------------------------------------------------
    # Create the Layer in GeoServer from the table
    # ------------------------------------------------------
    try:
        cat = Catalog(settings.GEOSERVER_BASE_URL + "rest",\
                    settings.GEOSERVER_CREDENTIALS[0],\
                    settings.GEOSERVER_CREDENTIALS[1])
                    #      "admin", "geoserver")
        workspace = cat.get_workspace("geonode")
        ds_list = cat.get_xml(workspace.datastore_url)
        datastores = [datastore_from_index(cat, workspace, n) for n in ds_list.findall("dataStore")]
        #----------------------------
        # Find the datastore
        #----------------------------
        ds = None
        from geonode.maps.utils import get_db_store_name
        for datastore in datastores:
            if datastore.name == get_db_store_name():
                ds = datastore

        if ds is None:
            err_msg = "Datastore '%s' not found" % (settings.DB_DATASTORE_NAME)
            return False, err_msg
        ft = cat.publish_featuretype(table_name, ds, "EPSG:4326", srs="EPSG:4326")
        cat.save(ft)
    except Exception as e:
        lat_lnt_map_record.delete()
        traceback.print_exc(sys.exc_info())
        err_msg = "Error creating GeoServer layer for %s: %s" % (table_name, str(e))
        return False, err_msg

    msg('create_point_col_from_lat_lon - 5 - add style')

     # ------------------------------------------------------
    # Set the Layer's default Style
    # ------------------------------------------------------
    set_default_style_for_latlng_layer(cat, ft)


    # ------------------------------------------------------
    # Create the Layer in GeoNode from the GeoServer Layer
    # ------------------------------------------------------
    try:
        layer, created = Layer.objects.get_or_create(name=table_name, defaults={
            "workspace": workspace.name,
            "store": ds.name,
            "storeType": ds.resource_type,
            "typename": "%s:%s" % (workspace.name.encode('utf-8'), ft.name.encode('utf-8')),
            "title": dt.title or 'No title provided',
            #"name" : dt.title or 'No title provided',
            "abstract": dt.abstract or 'No abstract provided',
            "uuid": str(uuid.uuid4()),
            "owner" : new_table_owner,
            #"bbox_x0": Decimal(ft.latlon_bbox[0]),
            #"bbox_x1": Decimal(ft.latlon_bbox[1]),
            #"bbox_y0": Decimal(ft.latlon_bbox[2]),
            #"bbox_y1": Decimal(ft.latlon_bbox[3])
        })
        #set_attributes(layer, overwrite=True)
    except Exception as e:
        traceback.print_exc(sys.exc_info())
        err_msg = "Error creating GeoNode layer for %s: %s" % (table_name, str(e))
        return False, err_msg

    # ----------------------------------
    # Set default permissions (public)
    # ----------------------------------
    layer.set_default_permissions()

    # ------------------------------------------------------------------
    # Create LayerAttributes for the new Layer (not done in GeoNode 2.x)
    # ------------------------------------------------------------------
    (attributes_created, err_msg) = create_layer_attributes_from_datatable(dt, layer)
    if not attributes_created:
        LOGGER.error(err_msg)
        layer.delete()  # Delete the layer
        return False, "Sorry there was an error creating the Datatable. (s:ll)"

    # ----------------------------------
    # Save a related LatLngTableMappingRecord
    # ----------------------------------
    lat_lnt_map_record.layer = layer

    # ----------------------------------
    # Retrieve matche/unmatched counts
    # ----------------------------------
    # Get datatable feature count - total record to map
    (success_datatable, datatable_feature_count) = get_layer_feature_count(dt.table_name)

    # Get layer feature count - mapped records
    (success_layer, layer_feature_count) = get_layer_feature_count(layer.name)

    # Set Record counts
    if success_layer and success_datatable:
        lat_lnt_map_record.mapped_record_count = layer_feature_count
        new_misssed_records = datatable_feature_count - layer_feature_count
        if lat_lnt_map_record.unmapped_record_count and lat_lnt_map_record.unmapped_record_count > 0:
            lat_lnt_map_record.unmapped_record_count += new_misssed_records
        else:
            lat_lnt_map_record.unmapped_record_count = new_misssed_records

    else:
        LOGGER.error('Failed to calculate Lat/Lng record counts')

    lat_lnt_map_record.save()

    return True, lat_lnt_map_record

def remove_bad_lat_lng_numbers(lat_lng_map_record):
    """
    Before trying map a DataTable into a Layer,
    remove any invalid lat/lng values.
    """
    if not isinstance(lat_lng_map_record, LatLngTableMappingRecord):
        return (False, "lat_lnt_map_record must be a LatLngTableMappingRecord object")

    if not lat_lng_map_record.datatable:
        return (False, "The LatLngTableMappingRecord must have a 'datatable'")
    LOGGER.info('remove_bad_lat_lng_numbers 1')

    # This is the SQL table to work with
    datatable_name = lat_lng_map_record.datatable.table_name

    # Build the Lat/Lng clause
    (worked, lat_lng_clause_or_err_msg) = get_lat_lng_clause(\
                    lat_lng_map_record.lat_attribute.attribute,\
                    lat_lng_map_record.lng_attribute.attribute)

    LOGGER.info('remove_bad_lat_lng_numbers 2')

    if not worked:
        user_msg = 'There was an error checking the Lat/Lng columns (1)'
        LOGGER.error('%s\n%s', user_msg, lat_lng_clause_or_err_msg)
        return False, user_msg

    if lat_lng_clause_or_err_msg is None or len(lat_lng_clause_or_err_msg)==0:
        user_msg = 'There was an error checking the Lat/Lng columns (2)'
        LOGGER.error('%s\n%s', user_msg, lat_lng_clause_or_err_msg)
        return False, user_msg


    LOGGER.info('remove_bad_lat_lng_numbers 3')

    # Are there any bad rows?
    #
    count_query = 'SELECT COUNT(*) from {0} WHERE {1};'.format(\
                datatable_name, lat_lng_clause_or_err_msg)

    # Retrieve them to save for error messages
    #
    retrieve_query = 'SELECT * from {0} WHERE {1};'.format(\
                datatable_name, lat_lng_clause_or_err_msg)

    # Delete them before proceeding with mapping
    #
    delete_query ='DELETE from {0} WHERE {1};'.format(\
                datatable_name, lat_lng_clause_or_err_msg)

    try:
        conn = psycopg2.connect(get_datastore_connection_string(is_dataverse_db=False))
        cur = conn.cursor()

        # Are there any bad rows?
        #
        LOGGER.info('remove_bad_lat_lng_numbers 4: %s', count_query)

        cur.execute(count_query)
        bad_row_count = cur.fetchone()[0]
        LOGGER.info("Bad row count: %s", bad_row_count)
        if bad_row_count == 0:
            return True, bad_row_count

        # Grab the bad rows, and save them
        # in the lat_lng_map_record
        #
        LOGGER.info('remove_bad_lat_lng_numbers 5: %s', retrieve_query)

        cur.execute(retrieve_query)
        (worked, err_msg) = save_bad_latlng_rows(lat_lng_map_record, cur.fetchall())
        LOGGER.info("Saved Bad row count? %s", worked)
        if not worked:
            return False, err_msg

        # Delete the bad rows from the table
        #
        cur.execute(delete_query)
        conn.commit()
        return True, bad_row_count

    except Exception as e:
        msg('failure...')
        msg(e)
        traceback.print_exc(sys.exc_info())
        err_msg = "Error remove bad rows for SQL table %s: %s" % (datatable_name, str(e))
        LOGGER.error(err_msg)
        return False, err_msg

    finally:
        conn.close()


def save_bad_latlng_rows(lat_lng_map_record, bad_rows):
    """
    These are rows where the lat/lng values are out of bounds.
    Save them to the LatLngTableMappingRecord as JSON
    """
    if not isinstance(lat_lng_map_record, LatLngTableMappingRecord):
        err_msg = "lat_lng_map_record must be a LatLngTableMappingRecord"
        LOGGER.error(err_msg)
        return False, err_msg

    if bad_rows is None:
        err_msg = "The rows with bad Lat/Lng values cannot be None"
        LOGGER.error(err_msg)
        return False, err_msg

    if len(bad_rows)==0:
        err_msg = "There must be at least one row with bad Lat/Lng values cannot be None"
        LOGGER.error(err_msg)
        return False, err_msg

    date_handler = lambda obj: (
        obj.isoformat()
        if isinstance(obj, datetime.datetime)
        or isinstance(obj, datetime.date)
        or isinstance(obj, datetime.time)
        else None
        )

    try:
        bad_rows_as_json = json.dumps(bad_rows, default=date_handler)
    except TypeError as e:
        err_msg = "Failed to convert bad rows to JSON: %s" % e.message
        LOGGER.error("Failed to convert bad rows to JSON")
        return False, err_msg

    lat_lng_map_record.unmapped_records_list = bad_rows_as_json

    lat_lng_map_record.save()

    return True, 'bad rows saved'

def get_lat_lng_clause(lat_colname, lng_colname):
    """
    Clause to filter rows where the lat or lng values are out of range
    """
    if lat_colname is None or lng_colname is None:
        return False,\
            "The lat_colname (%s) and lng_colname (%s) cannot be None"\
             % (lat_colname, lng_colname)

    clause = """{0} > 90 OR {0} < -90 OR {1} > 180 OR {1} < -180""".format(\
       lat_colname, lng_colname)
    return True, clause



    """
    - SELECT * from TABLE
        WHERE lat_col_attr > 90 or lat_col_attr < -90
            or lng_col_attr > 180 or lng_col_attr < -180;
    - Store these records in lat_lnt_map_record under unmapped_records_list
        - Make these a JSON field?- Once code is working well, save notebook and use AWS, local university or other service to run regularly**
    - Delete these records:
        DELETE from TABLE WHERE lat_col_attr > 90 or lat_col_attr < -90
        or lng_col_attr > 180 or lng_col_attr < -180;
    """

def get_layer_feature_count(table_name):
    """
    Given a table return the number of features--in this case the number of rows.
    """

    if table_name is None:
        LOGGER.error("Expected a table name")
        return (False, "Expected a table object")

    # e.g. geonode:coded_data_2008_10 => coded_data_2008_10
    table_name = table_name.split(':')[-1]

    layer = Layer.objects.get(name=table_name)

    # format SQL
    num_features_sql = 'SELECT COUNT(*) from {0};'.format(table_name)

    #print '%s num_features_sql: %s' % (table_name, num_features_sql)

    # Make the query
    try:
        conn = psycopg2.connect(get_datastore_connection_string(db_name=layer.store))
        cur = conn.cursor()
        cur.execute(num_features_sql)
        return (True, cur.fetchone()[0])
    except Exception as e:
        traceback.print_exc(sys.exc_info())
        err_msg =  "Error querying table %s:%s" % (table_name, str(e))
        LOGGER.error(err_msg)
        return (False, err_msg)
    finally:
        conn.close()


"""
import psycopg2
from geonode.contrib.datatables.db_helper import get_datastore_connection_string
from geonode.contrib.datatables.utils_lat_lng import get_lat_lng_clause

conn = psycopg2.connect(get_datastore_connection_string())
cur = conn.cursor()

clause = get_lat_lng_clause('latitude', 'longitude')
s="select count(*) from coded_data_2007_09_9r WHERE %s;" % (clause)
cur.execute(s)
bad_cnt = cur.fetchone()[0]
if bad_cnt > 0:
    s2="select * from coded_data_2007_09_9r WHERE %s;" % (clause)
    cur.execute(s)
    cur.fetchall()

cur.execute('delete from coded_data_2007_09_9r where latitude > 90 order by latitude limit 1;')


"""
