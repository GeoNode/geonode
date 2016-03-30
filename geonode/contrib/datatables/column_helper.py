"""
Convenience methods to:
    (1) Return the PostGres datatype of a given column
    (2) Determine whether that datatype fits into the broad category of either:
        (a) numeric data
        (b) character data

Used before attempting a SQL join between a Layer column and a DataTable column.
"""
import sys
import traceback
import logging
import psycopg2
from geonode.contrib.msg_util import msg, msgt
from geonode.contrib.datatables.db_helper import get_datastore_connection_string

LOGGER = logging.getLogger('geonode.contrib.datatables.column_helper')


POSTGRES_CHAR_DATATYPES = ('character varying', 'varchar', 'character',\
                            'char', 'text')
POSTGRES_NUMERIC_DATATYPES = ('smallint', 'integer', 'bigint', 'decimal',\
                            'numeric', 'real', 'double precision',\
                            'smallserial', 'serial', 'bigserial')


class ColumnHelper(object):

    @staticmethod
    def get_column_datatype(table_name, table_attribute):
        """
        Retrieve the column data type from postgres
        """
        if table_name is None or table_attribute is None:
            return (False, "The table_name and table_attribute must be specified.")

        table_name = table_name.split(':')[-1]  # e.g. geonode:some-table-name

        sql_target_data_type = "SELECT data_type " +\
                "FROM information_schema.columns " +\
                "WHERE table_name = '{0}' AND column_name='{1}';".format(\
                table_name, table_attribute)

        #msg ('sql_target_data_type: %s' % sql_target_data_type)

        try:
            conn = psycopg2.connect(get_datastore_connection_string())
            cur = conn.cursor()
            cur.execute(sql_target_data_type)
            data_type = cur.fetchone()[0]
            return (True, data_type)
        except Exception as e:
            traceback.print_exc(sys.exc_info())
            err_msg = "Error finding data type for column '%s' in table '%s': %s"\
                    % (table_attribute, table_name, str(e[0]))
            LOGGER.error(err_msg)
            return (False, err_msg)
        finally:
            conn.close()

    @staticmethod
    def is_char_column_conversion_recommended(table_name, table_attribute):
        """
        Hackish stuff here.
        This is for an issue where csvkit will turn a string containing
        digits into a number--e.g. even if double quoted, e.g. "123", csvkit
        makes it into a number
        """

        success, data_type_or_err_msg = ColumnHelper.get_column_datatype(table_name, table_attribute)
        if success:
            return (True, ColumnHelper.is_character_column(data_type_or_err_msg))
        else:
            return False, data_type_or_err_msg

    @staticmethod
    def is_character_column(data_type):
        """
        Check the data_type string against known postgres character datatypes
        """
        #global POSTGRES_CHAR_DATATYPES
        if data_type is None:
            return False

        if data_type in POSTGRES_CHAR_DATATYPES:
            return True

        return False

    @staticmethod
    def is_numeric_column(data_type):
        """
        Check the data_type string against known postgres numeric datatypes
        """
        #global POSTGRES_NUMERIC_DATATYPES
        if data_type is None:
            return False

        if data_type in POSTGRES_NUMERIC_DATATYPES:
            return True

        return False
