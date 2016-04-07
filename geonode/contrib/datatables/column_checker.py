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
from geonode.contrib.msg_util import msg, msgt
from geonode.contrib.datatables.db_helper import get_datastore_connection_string

LOGGER = logging.getLogger('geonode.contrib.datatables.column_checker')

from geonode.contrib.datatables.column_helper import ColumnHelper


class ColumnChecker(object):
    """
    Check the types of Postgres columns before trying to join them

    Example
    column_checker = ColumnChecker(layer_name, layer_attribute_name,
                            datatable_name, datatable_attribute_name)

    # (1) are_join_columns_compatible?

    (success, user_err_msg) = column_checker.are_join_columns_compatible()
    if success:
        print 'ok to join'
    else:
        print 'failed b/c: %s' % user_err_msg

    # (2) get_column_join_stmt(with_casting=True)

    (success, join_stmt_or_err_msg) = column_checker.get_column_join_stmt()
    if success:
        print 'yes, here is the join clause'
        return join_stmt_or_err_msg
    else:
        print 'nope'
        return join_stmt_or_err_msg
    """
    def __init__(self, target_table, target_attribute, dt_table, dt_attribute):
        self.target_table = target_table
        self.target_attribute = target_attribute
        self.dt_table = dt_table
        self.dt_attribute = dt_attribute


    def is_character_column(self, data_type):
        """
        Check the data_type string against known postgres character datatypes
        """
        return ColumnHelper.is_character_column(data_type)

    def is_numeric_column(self, data_type):
        """
        Check the data_type string against known postgres character datatypes
        """
        return ColumnHelper.is_numeric_column(data_type)

    def get_column_join_stmt(self, with_casting=True):
        """
        when creating a Table csvkit turns quoted

        Join statement possibilities:

        (1) same type
            target_table."attribute name A" = data_table."attribute name B"

        (2) target is char, DataTable is numeric

            Currently, returns an error.

            Commented out: you can explicitly alter the DataTable column, changing it from
            numeric to character.  This is great for combined Upload + Join
            commands.  However, it is dangerous if trying to join to an
            already uplodated DataTable.

        (3) target is numeric, datatable is char

            Doesn't work.  We don't want to explicitly change the target layer

        (4) one of the attributes is unknown

            error message

        (True, join_stmt)
        (False, error message)
        """

        # Target layer, join column data type
        (retrieved, target_data_type) = ColumnHelper.get_column_datatype(\
                            self.target_table, self.target_attribute)
        if not retrieved:
            return (False, 'Sorry, the target column is not available.')

        # Table to join, column data type
        (was_retrieved, datatable_data_type) =\
            ColumnHelper.get_column_datatype(self.dt_table, self.dt_attribute)
        if not was_retrieved:
            return (False, 'The data type of your column was not available')

        join_clause = '%s."%s" = %s."%s"' % (self.target_table,\
                                self.target_attribute,\
                                self.dt_table,\
                                self.dt_attribute)

        varchar_str = '::varchar'

        # Are columns types the same?  OK
        if target_data_type == datatable_data_type:
            return (True, join_clause)

        """
        msgt('%s.%s' % (self.target_table,\
                                self.target_attribute))
        msg('target_data_type: %s' % target_data_type)
        msg('target_data_type is_character_column: %s' % self.is_character_column(target_data_type))

        msg('target_data_type is_numeric_column: %s' % self.is_numeric_column(target_data_type))
        msgt('%s.%s' % (self.dt_table,\
                self.dt_attribute))

        msg('datatable_data_type: %s' % datatable_data_type)
        msg('datatable_data_type is_character_column: %s' % self.is_character_column(datatable_data_type))
        msg('datatable_data_type is_numeric_column: %s' % self.is_numeric_column(datatable_data_type))
        """
        # Are columns types both character? OK
        #
        if self.is_character_column(target_data_type) and\
            self.is_character_column(datatable_data_type):
            return (True, join_clause)

        # Are columns types both numeric? OK
        #
        if self.is_numeric_column(target_data_type) and\
            self.is_numeric_column(datatable_data_type):
            return (True, join_clause)

        if with_casting is True:
            #   Target is char but datatable is numeric,
            #   Cast datatable to varchar
            #

            if self.is_character_column(target_data_type) and\
                self.is_numeric_column(datatable_data_type):
                pass
                """
                #Handling this upstream instead, explicitly changing
                #DataTable upload to force a specified column to be char

                success, msg = self.alter_column_to_var(self.dt_table,\
                                self.dt_attribute)
                if success:
                    return True, join_clause
                else:
                    return False, msg
                """

            #   Target is char but datatable is numeric,
            #   Cast datatable COLUMN to varchar
            #
            if self.is_numeric_column(target_data_type) and\
                self.is_character_column(datatable_data_type):
                pass


        target_type_text = self.get_type_text_char_or_numeric(target_data_type)
        dt_type_text = self.get_type_text_char_or_numeric(datatable_data_type)

        err_msg = '<br />Your chosen column "{0}" is type {1}.  However, the chosen layer column "{2}" is type {3}'.format(\
                self.dt_attribute, dt_type_text, self.target_attribute, target_type_text)

        return (False, err_msg)


    def alter_column_to_var(self, table_name, attr_name):

        if table_name is None:
            return False, 'table_name cannot be None'

        if attr_name is None:
            return False, 'attr_name cannot be None'

        stmt = "ALTER TABLE {0} ALTER COLUMN".format(table_name) + \
            " {0} TYPE varchar(255) USING {0}::varchar;".format(attr_name)

        try:
            conn = psycopg2.connect(get_datastore_connection_string())

            cur = conn.cursor()
            cur.execute(stmt)
            conn.commit()
            return True, None

        except Exception as e:
            LOGGER.error('Exception running SQL stmt %s:\n%s', stmt, e)
            return False, "Error when trying to convert numeric column to character"
        finally:
            conn.close()
        #ALTER TABLE presales ALTER COLUMN code TYPE numeric(10,0) USING code::numeric;


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
        (retrieved, target_data_type) = ColumnHelper.get_column_datatype(\
                    self.target_table, self.target_attribute)
        if not retrieved:
            return (False, 'Sorry, the target column is not available.')

        # Table to join, column data type
        (was_retrieved, datatable_data_type) = ColumnHelper.get_column_datatype(\
                self.dt_table, self.dt_attribute)
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

        err_msg = '<br />Your chosen column "{0}" is type {1}.  However, the chosen layer column "{2}" is type {3}'.format(\
        self.dt_attribute, dt_type_text, self.target_attribute, target_type_text)

        return (False, err_msg)

    def get_type_text_char_or_numeric(self, data_type):
        """
        Help for formatting an error message
        """
        if data_type is None:
            return None

        if self.is_character_column(data_type):
            return 'a "character"'
        elif self.is_numeric_column(data_type):
            return 'a "numeric"'
        else:
            return 'neither a character nor a numeric'
