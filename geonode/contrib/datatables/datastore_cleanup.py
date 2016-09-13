from django.conf import settings
from geonode.maps.models import Layer
from geonode.contrib.datatables.models import DataTable
from geonode.contrib.datatables.db_helper import get_datastore_connection_string

"""
When deleting a geonode Layer, also delete it's corresponding table
"""
'''
def drop_datatable_from_store(data_table):

    if data_table is None:
        return
    if settings.DB_DATASTORE is not True:   # We are not storing layers as separate PostGIS tables
        return

    assert isinstance(data_table, DataTable), \
        "data_table must be a DataTable object (geonode.contrib.datatables.models.DataTable)"

    drop_table_sql = "DROP TABLE %s;" % (data_table.table_name)

    try:
        conn = psycopg2.connect(get_datastore_connection_string())

        cur = conn.cursor()
        cur.execute(drop_table_sql)
        conn.commit()
        conn.close()
    except Exception as e:
        conn.close()
        msg =  "Error Deleting DataTable '%s' from postgis Datastore." \
                    % (data_table.table_name, str(e[0]))
        return None, msg
'''
