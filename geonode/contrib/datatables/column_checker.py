"""
Before attempting a SQL join between a Layer column and a DataTable column,
compare the column types--the Postgres data types.

Check that a character column isn't going to be joined to a numeric column.
(see "ColumnChecker.are_join_columns_compatible()")

Attempting such a join will throw a Postgres error anyway--this is give a better
error message.
"""
import logging
import psycopg2
from geonode.contrib.msg_util import *
from geonode.contrib.datatables.db_helper import get_datastore_connection_string

logger = logging.getLogger('geonode.contrib.datatables.column_checker')


POSTGRES_CHAR_DATATYPES = ('character varying', 'varchar', 'character',
                            'char', 'text')
POSTGRES_NUMERIC_DATATYPES = ('smallint', 'integer', 'bigint', 'decimal',
                            'numeric', 'real', 'double precision',
                            'smallserial', 'serial', 'bigserial')

class ColumnChecker(object):

    def __init__(self, target_table, target_attribute, dt_table, dt_atrribute):
        self.target_table = target_table
        self.target_attribute = target_attribute
        self.dt_table = dt_table
        self.dt_atrribute = dt_atrribute


    def is_character_column(self, data_type):
        global POSTGRES_CHAR_DATATYPES
        if data_type is None:
            return False

        if data_type in POSTGRES_CHAR_DATATYPES:
            return True

        return False

    def is_numeric_column(self, data_type):
        global POSTGRES_NUMERIC_DATATYPES
        if data_type is None:
            return False

        if data_type in POSTGRES_NUMERIC_DATATYPES:
            return True

        return False

    @staticmethod
    def get_column_datatype(table_name, table_attribute):
        """
        Retrieve the column data type from postgres
        """
        if table_name is None or table_attribute is None:
            return (False, "The table_name and table_attribute must be specified.")

        sql_target_data_type = """SELECT data_type FROM information_schema.columns WHERE table_name = '{0}' AND column_name='{1}';""".format(table_name, table_attribute)

        msg ('sql_target_data_type: %s' % sql_target_data_type)

        try:
            conn = psycopg2.connect(get_datastore_connection_string())

            cur = conn.cursor()
            cur.execute(sql_target_data_type)
            data_type = cur.fetchone()[0]
            conn.close()
            return (True, data_type)

        except Exception as e:
            if conn:
                conn.close()

            import traceback
            traceback.print_exc(sys.exc_info())
            err_msg =  "Error finding data type for column '%s' in table '%s'" % (table_name, attribute_name, str(e[0]))
            logger.error(err_msg)
            return (False, err_msg)


    def are_join_columns_compatible(self):
        """
        Before attempting a join, make sure that the columns are compatible.
        Note: this should ideally be caught by the client using the API

        This is rough check to make sure a string isn't being joined to a number
        Not trying any casting or transformation here...yet

        Example case:  Attempt to join by census tract where target is char e.g. '000125'
            However, the user's table is numberic (b/c of Excel) e.g. 125
        """

        # Target layer, join column data type
        (retrieved, target_data_type) = ColumnChecker.get_column_datatype(self.target_table, self.target_attribute)
        if not retrieved:
            return (False, 'Sorry, the target column is not available.')

        # Table to join, column data type
        (was_retrieved, datatable_data_type) = ColumnChecker.get_column_datatype(self.dt_table, self.dt_atrribute)
        if not was_retrieved:
            return (False, 'The data type of your column was not available')

        # Are columns types the same?  OK
        if target_data_type == datatable_data_type:
            return (True, None)

        # Are columns types both character? OK
        #
        if self.is_character_column(target_data_type) and\
            self.is_character_column(datatable_data_type):
            return (True, None)

        # Are columns types both numeric? OK
        #
        if self.is_numeric_column(target_data_type) and\
            self.is_numeric_column(datatable_data_type):
            return (True, None)

        target_type_text = self.get_type_text_char_or_numeric(target_data_type)
        dt_type_text = self.get_type_text_char_or_numeric(datatable_data_type)

        err_msg = '<br />Your chosen column "{0}" has {1} column.  However, the chosen layer has {3} column'.format(\
                self.dt_atrribute, dt_type_text, self.target_attribute, target_type_text)
        return (False, err_msg)


    def get_type_text_char_or_numeric(self, data_type):
        if data_type is None:
            return None

        if self.is_character_column(data_type):
            return 'a "character"'
        elif self.is_numeric_column(data_type):
            return 'a "numeric"'
        else:
            'neither a character nor a numeric'
