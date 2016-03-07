"""
SQL calls related to Table Joins
"""
import sys
import traceback
import logging

import psycopg2

from django.template.defaultfilters import slugify

from geonode.contrib.datatables.models import TableJoin
from geonode.contrib.datatables.db_helper import get_datastore_connection_string

LOGGER = logging.getLogger(__name__)

def drop_view_from_table_join(table_join):
    """
    Given a view name, drop it from the database
    """
    if not isinstance(table_join, TableJoin):
        return False, "table_join must be a TableJoin object"

    view_name = table_join.view_name
    if view_name is None or len(view_name) < 5:
        return False, 'The TableJoin layer (view) could not be found.'

    # -----------------------------------------------------
    # Execute the SQL and Drop the View
    # -----------------------------------------------------
    conn = psycopg2.connect(get_datastore_connection_string())

    try:
        cur = conn.cursor()
        cur.execute('DROP VIEW IF EXISTS %s;' % view_name)
        conn.commit()
        return True, None
    except Exception as e:
        traceback.print_exc(sys.exc_info())
        err_msg = ("Error dropping view {0} "
                "from table join (id: {1})"
                "\n(For admins: {2})".format(\
                view_name, table_join.id, str(e)))
        LOGGER.error(err_msg)
        return False, err_msg
    finally:
        conn.close()

def does_table_name_exist(table_name):
    """
    Check if a table or view name already exists by using a
    Postgres select statement
    """
    assert table_name is not None, "The table_name cannot be None"

    # For safety, slugify the name...
    table_name = slugify(table_name)

    stmt_count = ("SELECT COUNT(table_name) "
            "FROM information_schema.tables "
            "WHERE table_schema='public' "
            "AND table_name = '{0}'';".format(\
            table_name))

    conn = psycopg2.connect(get_datastore_connection_string())

    try:
        cur = conn.cursor()
        cur.execute(stmt_count)
        cnt = cur.fetchone()[0]
        if cnt > 0:
            return True
        else:
            return False
    except Exception as e:
        traceback.print_exc(sys.exc_info())
        err_msg = ("Error running SQL SELECT: {0}:\n{1}".format(\
                    stmt_count, str(e)))
        LOGGER.error(err_msg)
        return False
    finally:
        conn.close()
