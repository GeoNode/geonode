#from __future__ import print_function
import sys
import os
import os
import glob
import uuid
import csvkit
import logging
from decimal import Decimal
import string
from random import choice
from csvkit import sql
from csvkit import table
from csvkit import CSVKitWriter
from csvkit.cli import CSVKitUtility

from geoserver.catalog import Catalog
from geoserver.store import datastore_from_index
from geoserver.resource import FeatureType

import psycopg2
from psycopg2.extensions import QuotedString

from django.template.defaultfilters import slugify
from django.core.files import File
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from geonode.maps.models import Layer, LayerAttribute
from geonode.maps.gs_helpers import get_sld_for #fixup_style, cascading_delete, delete_from_postgis, get_postgis_bbox

from geonode.contrib.msg_util import *

from .models import DataTable, DataTableAttribute, TableJoin
from .db_helper import get_datastore_connection_string
from .layer_helper import create_geoserver_and_geonode_layers, set_default_style_for_new_layer, create_layer_attributes_from_datatable

logger = logging.getLogger('geonode.contrib.datatables.utils')

THE_GEOM_LAYER_COLUMN = 'the_geom'
THE_GEOM_LAYER_COLUMN_REPLACEMENT = 'the_geom_col'

def standardize_name(col_name, is_table_name=False):
    """
    Format table and column names in tabular files
    """
    assert col_name is not None, "col_name cannot be None"

    if is_table_name:
       return slugify(unicode(col_name)).replace('-','_')

    cname = slugify(unicode(col_name)).replace('-','_')
    if cname == THE_GEOM_LAYER_COLUMN:
        return THE_GEOM_LAYER_COLUMN_REPLACEMENT
    return cname


def process_csv_file(data_table, delimiter=",", no_header_row=False):
    """
    Transform csv file and add it to the postgres DataStore

    :param instance:
    :param delimiter:
    :param no_header_row:
    :return:
    """
    assert isinstance(data_table, DataTable), "instance must be a DataTable object"

    # full path to csv file
    #
    csv_filename = data_table.uploaded_file.path

    # Standardize table_name for the DataTable
    #
    table_name = standardize_name(os.path.splitext(os.path.basename(csv_filename))[0], is_table_name=True)
    if table_name[:1].isdigit():
        table_name = 't-' + table_name
    #
    data_table.table_name = table_name
    data_table.save()

    # -----------------------------------------------------
    # Transform csv file to csvkit Table
    # -----------------------------------------------------
    f = open(csv_filename, 'rb')

    try:
        csv_table = table.Table.from_csv(f, name=table_name, no_header_row=no_header_row, delimiter=delimiter)
    except:
        data_table.delete()
        err_msg = str(sys.exc_info()[0])
        logger.error('Failed to convert csv file to table.  Error: %s' % err_msg)
        return None, err_msg
    #csv_file = File(f)
    f.close()


    msg ('process_csv_file 2')

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
            attribute, created = DataTableAttribute.objects.get_or_create(datatable=data_table,
                attribute=column.name,
                attribute_label=column.name,
                attribute_type=column.type.__name__,
                display_order=column.order)
    except:
        data_table.delete()     # Deleting DataTable also deletes related DataTableAttribute objects
        err_msg = 'Failed to convert csv file to table.  Error: %s' % str(sys.exc_info()[0])
        logger.error(err_msg)
        return None, err_msg


    msg ('process_csv_file 3')
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
        logger.error(err_msg)
        return None, err_msg


    msg ('process_csv_file 4')

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
        import traceback
        traceback.print_exc(sys.exc_info())
        err_msg =  "Error Creating table %s:%s" % (data_table.name, str(e))
        logger.error(err_msg)
        return None, err_msg

    finally:
        conn.close()
    msg ('process_csv_file 5')

    # -----------------------------------------------------
    # Copy Data to postgres csv data to Postgres
    # -----------------------------------------------------
    #connection_string = "postgresql://%s:%s@%s:%s/%s" % (db['USER'], db['PASSWORD'], db['HOST'], db['PORT'], db['NAME'])

    connection_string = get_datastore_connection_string(url_format=True)
    try:
        engine, metadata = sql.get_connection(connection_string)
    except ImportError:
        err_msg =  "Failed to get SQL connection for copying csv data to database.\n%s" % str(sys.exc_info()[0])
        logger.error(err_msg)
        return None, err_msg

    msg ('process_csv_file 6')

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
            logger.error(err_msg)
            return None, err_msg

    msg ('process_csv_file 7')

    # Commit new rows and close connection
    #
    trans.commit()
    conn.close()
    f.close()

    return data_table, ""


def create_point_col_from_lat_lon(new_table_owner, table_name, lat_column, lon_column):
    assert isinstance(new_table_owner, User), "new_table_owner must be a User object"

    msg('create_point_col_from_lat_lon - 1')
    try:
        dt = DataTable.objects.get(table_name=table_name)
    except:
        err_msg = "Error: (%s) %s" % (str(e), table_name)
        return None, err_msg

    msg('create_point_col_from_lat_lon - 2')

    #alter_table_sql = "ALTER TABLE %s ADD COLUMN geom geometry(POINT,4326);" % (table_name) # postgi 2.x
    alter_table_sql = "ALTER TABLE %s ADD COLUMN geom geometry;" % (table_name) # postgis 1.x
    update_table_sql = "UPDATE %s SET geom = ST_SetSRID(ST_MakePoint(%s,%s),4326);" % (table_name, lon_column, lat_column)
    #update_table_sql = "UPDATE %s SET geom = ST_SetSRID(ST_MakePoint(cast(%s AS float), cast(%s as float)),4326);" % (table_name, lon_column, lat_column)
    msg('update_table_sql: %s' % update_table_sql)
    create_index_sql = "CREATE INDEX idx_%s_geom ON %s USING GIST(geom);" % (table_name, table_name)

    msg('create_point_col_from_lat_lon - 3')

    if 1:
        conn = psycopg2.connect(get_datastore_connection_string())

        cur = conn.cursor()
        cur.execute(alter_table_sql)
        cur.execute(update_table_sql)
        cur.execute(create_index_sql)
        conn.commit()
        conn.close()
    #except Exception as e:
    #    conn.close()
    #    err_msg =  "Error Creating Point Column from Latitude and Longitude %s" % (str(e[0]))
    #    return None, err_msg

    msg('create_point_col_from_lat_lon - 4')

    # ------------------------------------------------------
    # Create the Layer in GeoServer from the table
    # ------------------------------------------------------
    try:
        cat = Catalog(settings.GEOSERVER_BASE_URL + "rest",
                          "admin", "geoserver")
        workspace = cat.get_workspace("geonode")
        ds_list = cat.get_xml(workspace.datastore_url)
        datastores = [datastore_from_index(cat, workspace, n) for n in ds_list.findall("dataStore")]
        #----------------------------
        # Find the datastore
        #----------------------------
        ds = None
        for datastore in datastores:
            #if datastore.name == "datastore":
            if datastore.name == settings.DB_DATASTORE_NAME: #"geonode_imports":
                ds = datastore

        if ds is None:
            err_msg = "Datastore '%s' not found" % (settings.DB_DATASTORE_NAME)
            return None, err_msg

        assert hasattr(cat, 'publish_featuretype'), 'cat does not have publish_featuretype'
        ft = cat.publish_featuretype(table_name, ds, "EPSG:4326", srs="EPSG:4326")
        cat.save(ft)
    except Exception as e:
        #tj.delete()
        import traceback
        traceback.print_exc(sys.exc_info())
        err_msg = "Error creating GeoServer layer for %s: %s" % (table_name, str(e))
        return None, err_msg

    msg('create_point_col_from_lat_lon - 5 - add style')

     # ------------------------------------------------------
    # Set the Layer's default Style
    # ------------------------------------------------------
    set_default_style_for_new_layer(cat, ft)


    # ------------------------------------------------------
    # Create the Layer in GeoNode from the GeoServer Layer
    # ------------------------------------------------------
    try:
        layer, created = Layer.objects.get_or_create(name=table_name, defaults={
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
        })
        #set_attributes(layer, overwrite=True)
    except Exception as e:
        import traceback
        traceback.print_exc(sys.exc_info())
        err_msg = "Error creating GeoNode layer for %s: %s" % (table_name, str(e))
        return None, err_msg

    # ----------------------------------
    # Set default permissions (public)
    # ----------------------------------
    layer.set_default_permissions()

    # ------------------------------------------------------------------
    # Create LayerAttributes for the new Layer (not done in GeoNode 2.x)
    # ------------------------------------------------------------------
    create_layer_attributes_from_datatable(dt, layer)


    return layer, ""


def setup_join(new_table_owner, table_name, layer_typename, table_attribute_name, layer_attribute_name):
    """
    Setup the Table Join in GeoNode
    """
    assert isinstance(new_table_owner, User), "new_table_owner must be a User object"
    assert table_name is not None, "table_name cannot be None"
    assert layer_typename is not None, "layer_typename cannot be None"
    assert table_attribute_name is not None, "table_attribute_name cannot be None"
    assert layer_attribute_name is not None, "layer_attribute_name cannot be None"

    # A bit broken up, but only for more specific error messages
    #
    try:
        dt = DataTable.objects.get(table_name=table_name)
    except DataTable.DoesNotExist:
        err_msg = 'DataTable not found with name: %s' % dt
        logger.error(err_msg)
        return None, err_msg

    try:
        table_attribute = dt.attributes.get(datatable=dt,attribute=table_attribute_name)
    except DataTableAttribute.DoesNotExist:
        err_msg = 'DataTableAttribute attribute not found with name: %s in table: %s' \
                            % (table_attribute_name, dt)
        logger.error(err_msg)
        return None, err_msg

    try:
        layer = Layer.objects.get(typename=layer_typename)
    except Layer.DoesNotExist:
        err_msg = 'Layer not found with typename: %s' % layer_typename
        logger.error(err_msg)
        return None, err_msg

    try:
        layer_attribute = layer.attributes.get(layer=layer, attribute=layer_attribute_name)
    except LayerAttribute.DoesNotExist:
        err_msg = 'LayerAttribute attribute not found with name: %s in layer: %s' % (layer_attribute_name, layer)
        logger.error(err_msg)
        return None, err_msg


    layer_name = layer.typename.split(':')[1]
    msg('setup_join 02')

    view_name = "join_%s_%s" % (layer_name, dt.table_name)

    view_sql = 'create view %s as select %s.%s, %s.* from %s inner join %s on %s."%s" = %s."%s";' %  (view_name, layer_name, THE_GEOM_LAYER_COLUMN, dt.table_name, layer_name, dt.table_name, layer_name, layer_attribute.attribute, dt.table_name, table_attribute.attribute)
    msg('view_sql: %s' % view_sql)
    #view_sql = 'create materialized view %s as select %s.the_geom, %s.* from %s inner join %s on %s."%s" = %s."%s";' %  (view_name, layer_name, dt.table_name, layer_name, dt.table_name, layer_name, layer_attribute.attribute, dt.table_name, table_attribute.attribute)

    #double_view_name = "view_%s" % view_name
    #double_view_sql = "create view %s as select * from %s" % (double_view_name, view_name)
    msg('setup_join 03')

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
    msg('setup_join 04')
    tj, created = TableJoin.objects.get_or_create(source_layer=layer, datatable=dt, table_attribute=table_attribute, layer_attribute=layer_attribute, view_name=view_name)#, view_name=double_view_name)
    tj.view_sql = view_sql

    msg('setup_join 05')

    # ------------------------------------------------------------------
    # Create the View (and double view)
    # ------------------------------------------------------------------
    try:
        conn = psycopg2.connect(get_datastore_connection_string())

        cur = conn.cursor()
        #cur.execute('drop view if exists %s;' % double_view_name)  # removing double view
        cur.execute('drop view if exists %s;' % view_name)
        #cur.execute('drop materialized view if exists %s;' % view_name)
        msg ('view_sql: %s'% view_sql)
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
    except Exception as e:
        if conn:
            conn.close()
        tj.delete() # remove the TableJoin object
        import traceback
        traceback.print_exc(sys.exc_info())
        err_msg =  "Error Joining table %s to layer %s: %s" % (table_name, layer_typename, str(e[0]))
        return None, err_msg


    msg('setup_join 06')

    #--------------------------------------------------
    # Create the Layer in GeoServer from the view
    #--------------------------------------------------
    new_geoserver_layer = None
    msg('setup_join 06a')

    success, err_or_geonode_layer = create_geoserver_and_geonode_layers(new_table_owner, view_name, dt, layer)
    if not success:
        tj.delete() # remove the TableJoin object
        logger.error('Failed to create layer. \nError: %s' % err_or_geonode_layer)
        return None, err_or_geonode_layer
    new_geonode_layer = err_or_geonode_layer
    msg('new_geonode_layer: %s' % new_geonode_layer)
    """
    try:
        cat = Catalog(settings.GEOSERVER_BASE_URL + "rest",
                          "admin", "geoserver")
        workspace = cat.get_workspace('geonode')
        ds_list = cat.get_xml(workspace.datastore_url)
        datastores = [datastore_from_index(cat, workspace, n) for n in ds_list.findall("dataStore")]
        #----------------------------
        # Find the datastore
        #----------------------------
        ds = None
        for datastore in datastores:
            #msg ('datastore name:', datastore.name)
            if datastore.name == settings.DB_DATASTORE_NAME: #"geonode_imports":
                ds = datastore
        if ds is None:
            tj.delete()
            err_msg = "Datastore name not found: %s" % settings.DB_DATASTORE_NAME
            logger.error(str(ds))
            return None, err_msg
        #print 'PRE PUBLISH'
        #assert hasattr(cat, 'publish_featuretype'), 'catalog does not have publish_featuretype'
        #print 'POST PUBLISH'

        from layer_helper import create_geonode_layer
        msg('setup_join 06a')

        success, err_or_geoserver_layer = create_geonode_layer(new_table_owner, view_name, dt, ds, layer)
        if not success:
            return None, err_or_geoserver_layer

        new_geoserver_layer = err_or_geoserver_layer
        msg('setup_join 06b')
        #ft = cat.publish_featuretype(view_name, ds, layer.srs, srs=layer.srs)
        #ft = cat.publish_featuretype(double_view_name, ds, layer.srs, srs=layer.srs)

        #cat.save(ft)
    except Exception as e:
        tj.delete()
        import traceback
        traceback.print_exc(sys.exc_info())
        err_msg = "Error creating GeoServer layer for %s: %s" % (view_name, str(e))
        return None, err_msg
    """

    # ------------------------------------------------------
    # Set the Layer's default Style
    # ------------------------------------------------------
    #set_default_style_for_new_layer(cat, ft)

    # ------------------------------------------------------------------
    # Create the Layer in GeoNode from the GeoServer Layer
    # ------------------------------------------------------------------
    """
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
        print 'layer_params', layer_params
        print 'view_name', view_name
        layer, created = Layer.objects.get_or_create(name=view_name, defaults=layer_params)

        # Set default permissions (public)
        layer.set_default_permissions()
        #set_attributes(layer, overwrite=True)

        tj.join_layer = layer
        tj.save()
    except Exception as e:
        tj.delete()
        import traceback
        traceback.print_exc(sys.exc_info())
        err_msg = "Error creating GeoNode layer for %s: %s" % (view_name, str(e))
        return None, err_msg
    """
    tj.join_layer = new_geonode_layer
    tj.save()

    print 'setup_join 08'
    # ------------------------------------------------------------------
    # Create LayerAttributes for the new Layer (not done in GeoNode 2.x)
    # ------------------------------------------------------------------
    #create_layer_attributes_from_datatable(dt, layer)


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
    msgt('SLD retrieved: %s' % sld)

    if sld is None:
        err_msg = 'Failed to retrieve the SLD for the geoserver layer: %s' % feature_type.name
        logger.error(err_msg)
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

