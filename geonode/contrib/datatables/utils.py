import sys
import os
import os
import glob
import uuid
import csvkit
import logging
from decimal import Decimal
from csvkit import sql
from csvkit import table
from csvkit import CSVKitWriter
from csvkit.cli import CSVKitUtility
from django.db.models import signals
from geoserver.catalog import Catalog
from geoserver.store import datastore_from_index
from geonode.geoserver.helpers import ogc_server_settings
from geonode.geoserver.signals import geoserver_pre_save

import psycopg2
from psycopg2.extensions import QuotedString

from django.utils.text import slugify
from django.core.files import File
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from geonode.layers.models import Layer, Attribute
from geonode.contrib.datatables.models import DataTable, TableJoin
from geonode.geoserver.helpers import set_attributes

_user = settings.OGC_SERVER['default']['USER']
_password = settings.OGC_SERVER['default']['PASSWORD']

logger = logging.getLogger('geonode.contrib.datatables.utils')

def process_csv_file(instance, delimiter=",", no_header_row=False):

    csv_filename = instance.uploaded_file.path
    table_name = slugify(unicode(os.path.splitext(os.path.basename(csv_filename))[0])).replace('-','_')
    if table_name[:1].isdigit():
        table_name = 'x' + table_name

    instance.table_name = table_name
    instance.save()
    f = open(csv_filename, 'rb')

    try:
        csv_table = table.Table.from_csv(f,name=table_name, no_header_row=no_header_row, delimiter=delimiter)
    except:
        instance.delete()
        return None, str(sys.exc_info()[0])

    csv_file = File(f)
    f.close()

    for column in csv_table:
        column.name = slugify(unicode(column.name)).replace('-','_')
        attribute, created = Attribute.objects.get_or_create(
            layer=instance,
            attribute=column.name,
            attribute_label=column.name,
            attribute_type=column.type.__name__,
            display_order=column.order)

    # Create Database Table
    try:
        sql_table = sql.make_table(csv_table,table_name)
        create_table_sql = sql.make_create_table_statement(sql_table, dialect="postgresql")
        instance.create_table_sql = create_table_sql
        instance.save()
    except:
        instance.delete()
        return None, str(sys.exc_info()[0])

    import psycopg2
    db = ogc_server_settings.datastore_db
    conn = psycopg2.connect("dbname='{0}' user='{1}' host='{2}' password='{3}' port={4}".format(
        db['NAME'], db['USER'], db['HOST'], db['PASSWORD'], db['PORT']))

    try:
        cur = conn.cursor()
        cur.execute('drop table if exists %s CASCADE;' % table_name)
        cur.execute(create_table_sql)
        conn.commit()
    except Exception as e:
        logger.error(
            "Error Creating table %s:%s",
            instance.name,
            str(e))
    finally:
        conn.close()

    # Copy Data to postgres
    connection_string = "postgresql://%s:%s@%s:%s/%s" % (db['USER'], db['PASSWORD'], db['HOST'], db['PORT'], db['NAME'])
    try:
        engine, metadata = sql.get_connection(connection_string)
    except ImportError:
        return None, str(sys.exc_info()[0])

    conn = engine.connect()
    trans = conn.begin()

    if csv_table.count_rows() > 0:
        insert = sql_table.insert()
        headers = csv_table.headers()
        try:
            conn.execute(insert, [dict(zip(headers, row)) for row in csv_table.to_rows()])
        except:
            # Clean up after ourselves
            instance.delete()
            return None, str(sys.exc_info()[0])

    trans.commit()
    conn.close()
    f.close()

    return instance, ""

def create_point_col_from_lat_lon(table_name, lat_column, lon_column):
    try:
        dt = DataTable.objects.get(table_name=table_name)
    except:
        msg = "Error: (%s) %s" % (str(e), table_name)
        return None, msg

    alter_table_sql = "ALTER TABLE %s ADD COLUMN geom geometry(POINT,4326);" % (table_name)
    update_table_sql = "UPDATE %s SET geom = ST_SetSRID(ST_MakePoint(%s,%s),4326);" % (table_name, lon_column, lat_column)
    create_index_sql = "CREATE INDEX idx_%s_geom ON %s USING GIST(geom);" % (table_name, table_name)

    try:
        db = ogc_server_settings.datastore_db
        conn = psycopg2.connect(
            "dbname='" +
            db['NAME'] +
            "' user='" +
            db['USER'] +
            "'  password='" +
            db['PASSWORD'] +
            "' port=" +
            db['PORT'] +
            " host='" +
            db['HOST'] +
            "'")
        cur = conn.cursor()
        cur.execute(alter_table_sql)
        cur.execute(update_table_sql)
        cur.execute(create_index_sql)
        conn.commit()
        conn.close()
    except Exception as e:
        conn.close()
        msg =  "Error Creating Point Column from Latitude and Longitude %s" % (str(e[0]))
        return None, msg

    # Create the Layer in GeoServer from the table
    try:
        cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + "rest",
                          _user, _password)
        workspace = cat.get_workspace(settings.DEFAULT_WORKSPACE)
        ds_list = cat.get_xml(workspace.datastore_url)
        datastores = [datastore_from_index(cat, workspace, n) for n in ds_list.findall("dataStore")]
        ds = None
        for datastore in datastores:
            if datastore.name == "datastore":
                ds = datastore
        ft = cat.publish_featuretype(table_name, ds, "EPSG:4326", srs="EPSG:4326")
        cat.save(ft)
    except Exception as e:
        tj.delete()
        msg = "Error creating GeoServer layer for %s: %s" % (table_name, str(e))
        return None, msg

    # Create the Layer in GeoNode from the GeoServer Layer
    try:
        signals.pre_save.disconnect(geoserver_pre_save, sender=Layer)
        layer, created = Layer.objects.get_or_create(name=table_name, defaults={
            "workspace": workspace.name,
            "store": ds.name,
            "storeType": ds.resource_type,
            "typename": "%s:%s" % (workspace.name.encode('utf-8'), ft.name.encode('utf-8')),
            "title": ft.title or 'No title provided',
            "abstract": ft.abstract or 'No abstract provided',
            "uuid": str(uuid.uuid4()),
            "bbox_x0": Decimal(ft.latlon_bbox[0]),
            "bbox_x1": Decimal(ft.latlon_bbox[1]),
            "bbox_y0": Decimal(ft.latlon_bbox[2]),
            "bbox_y1": Decimal(ft.latlon_bbox[3])
        })
        signals.pre_save.connect(geoserver_pre_save, sender=Layer)
        set_attributes(layer, overwrite=True)
    except Exception as e:
        msg = "Error creating GeoNode layer for %s: %s" % (table_name, str(e))
        return None, msg

    return layer, ""


def setup_join(table_name, layer_typename, table_attribute_name, layer_attribute_name):

    # Setup the Table Join in GeoNode
    try:
        dt = DataTable.objects.get(table_name=table_name)
        layer = Layer.objects.get(typename=layer_typename)
        table_attribute = dt.attributes.get(resource=dt,attribute=table_attribute_name)
        layer_attribute = layer.attributes.get(resource=layer, attribute=layer_attribute_name)
    except Exception as e:
        msg = "Error: (%s) %s:%s:%s:%s" % (str(e), table_name, layer_typename, table_attribute_name, layer_attribute_name)
        return None, msg

    layer_name = layer.typename.split(':')[1]
    view_name = "join_%s_%s" % (layer_name, dt.table_name)

    view_sql = 'create materialized view %s as select %s.the_geom, %s.* from %s inner join %s on %s."%s" = %s."%s";' %  (view_name, layer_name, dt.table_name, layer_name, dt.table_name, layer_name, layer_attribute.attribute, dt.table_name, table_attribute.attribute)
    double_view_name = "view_%s" % view_name
    double_view_sql = "create view %s as select * from %s" % (double_view_name, view_name)
    matched_count_sql = 'select count(%s) from %s where %s.%s in (select "%s" from %s);' % (table_attribute.attribute, dt.table_name, dt.table_name, table_attribute.attribute, layer_attribute.attribute, layer_name)
    unmatched_count_sql = 'select count(%s) from %s where %s.%s not in (select "%s" from %s);' % (table_attribute.attribute, dt.table_name, dt.table_name, table_attribute.attribute, layer_attribute.attribute, layer_name)
    unmatched_list_sql = 'select %s from %s where %s.%s not in (select "%s" from %s) limit 100;' % (table_attribute.attribute, dt.table_name, dt.table_name, table_attribute.attribute, layer_attribute.attribute, layer_name)
    tj, created = TableJoin.objects.get_or_create(source_layer=layer,datatable=dt, table_attribute=table_attribute, layer_attribute=layer_attribute, view_name=double_view_name)
    tj.view_sql = view_sql

    # Create the View (and double view)
    try:
        db = ogc_server_settings.datastore_db
        conn = psycopg2.connect(
            "dbname='" +
            db['NAME'] +
            "' user='" +
            db['USER'] +
            "'  password='" +
            db['PASSWORD'] +
            "' port=" +
            db['PORT'] +
            " host='" +
            db['HOST'] +
            "'")
        cur = conn.cursor()
        cur.execute('drop view if exists %s;' % double_view_name)
        cur.execute('drop materialized view if exists %s;' % view_name)
        cur.execute(view_sql)
        cur.execute(double_view_sql)
        cur.execute(matched_count_sql)
        tj.matched_records_count = cur.fetchone()[0]
        cur.execute(unmatched_count_sql)
        tj.unmatched_records_count = int(cur.fetchone()[0])
        cur.execute(unmatched_list_sql)
        tj.unmatched_records_list = ",".join([r[0] for r in cur.fetchall()])
        conn.commit()
        conn.close()
    except Exception as e:
        conn.close()
        tj.delete()
        msg =  "Error Joining table %s to layer %s: %s" % (table_name, layer_typename, str(e[0]))
        return None, msg

    # Create the Layer in GeoServer from the view
    try:
        cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + "rest",
                          _user, _password)
        workspace = cat.get_workspace(settings.DEFAULT_WORKSPACE)
        ds_list = cat.get_xml(workspace.datastore_url)
        datastores = [datastore_from_index(cat, workspace, n) for n in ds_list.findall("dataStore")]
        ds = None
        for datastore in datastores:
            if datastore.name == "datastore":
                ds = datastore
        ft = cat.publish_featuretype(double_view_name, ds, layer.srid, srs=layer.srid)
        cat.save(ft)
    except Exception as e:
        tj.delete()
        msg = "Error creating GeoServer layer for %s: %s" % (view_name, str(e))
        return None, msg

    # Create the Layer in GeoNode from the GeoServer Layer
    try:
        signals.pre_save.disconnect(geoserver_pre_save, sender=Layer)
        layer, created = Layer.objects.get_or_create(name=view_name, defaults={
            "workspace": workspace.name,
            "store": ds.name,
            "storeType": ds.resource_type,
            "typename": "%s:%s" % (workspace.name.encode('utf-8'), ft.name.encode('utf-8')),
            "title": ft.title or 'No title provided',
            "abstract": ft.abstract or 'No abstract provided',
            "uuid": str(uuid.uuid4()),
            "bbox_x0": Decimal(ft.latlon_bbox[0]),
            "bbox_x1": Decimal(ft.latlon_bbox[1]),
            "bbox_y0": Decimal(ft.latlon_bbox[2]),
            "bbox_y1": Decimal(ft.latlon_bbox[3])
        })
        signals.pre_save.connect(geoserver_pre_save, sender=Layer)
        set_attributes(layer, overwrite=True)
        tj.join_layer = layer
        tj.save()
    except Exception as e:
        tj.delete()
        msg = "Error creating GeoNode layer for %s: %s" % (view_name, str(e))
        return None, msg

    return tj, ""
