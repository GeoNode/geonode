import string
from random import choice

from django.template.defaultfilters import slugify

from geonode.contrib.datatables.models import DataTable
from geonode.contrib.datatables.utils_joins import does_table_name_exist

THE_GEOM_LAYER_COLUMN = 'the_geom'
THE_GEOM_LAYER_COLUMN_REPLACEMENT = 'the_geom_col'


def standardize_column_name(col_name):
    """
    Format column names in tabular files
     - Handle special case for columns named "the_geom", replace them
    """
    assert col_name is not None, "col_name cannot be None"

    cname = slugify(unicode(col_name)).replace('-', '_')
    if cname == THE_GEOM_LAYER_COLUMN:
        return THE_GEOM_LAYER_COLUMN_REPLACEMENT
    return cname


def standardize_table_name(tbl_name):
    """
    Make sure table name:
        - Doesn't begin with a number
        - Has "-" instead of '_'
        - Truncate name
    """
    assert tbl_name is not None, "tbl_name cannot be None"
    assert len(tbl_name) > 0, "tbl_name must be a least 1-char long, not zero"

    if tbl_name[:1].isdigit():
        tbl_name = 't_' + tbl_name

    tname = slugify(unicode(tbl_name)).replace('-', '_')[:11]
    if tname.endswith('_'):
        return tname[:-1]

    return tname

def get_random_chars(num_chars=1):
    """
    Return a random string of lowercase letters and digits
    """
    char_list = string.ascii_lowercase + string.digits
    return "".join([choice(char_list) for i in range(num_chars)])


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
        random_chars = get_random_chars(x+1)
        unique_tname = '%s_%s' % (table_name, random_chars)
    # ------------------------------------------------
    # Failed to generate a unique name, throw an error
    # ------------------------------------------------
    err_msg = """Failed to generate unique table_name attribute for a new DataTable object.
Original: %s
Attempts: %s""" % (table_name, ', '.join(attempts))
    raise ValueError(err_msg)


def get_unique_viewname(layer_name, table_name):
    """
    When making a View to represent a TableJoin, make sure the name
    isn't already in the database
    """
    assert layer_name is not None, "layer_name cannot be None"
    assert table_name is not None, "table_name cannot be None"

    # ------------------------------------------------
    # slugify, change to unicode
    # ------------------------------------------------
    view_name = 'j_{0}_{1}'.format(\
                standardize_table_name(layer_name),
                standardize_table_name(table_name))
    if view_name.endswith('_'):
        view_name = view_name[:-1]

    # ------------------------------------------------
    # Make 10 attempts to generate a unique view name
    # ------------------------------------------------
    unique_vname = view_name
    attempts = []
    for x in range(1, 11):
        attempts.append(unique_vname)   # save the attempt

        # Is this a unique name?  Yes, return it.
        if not does_table_name_exist(unique_vname):
            return unique_vname

        # Not unique. Add 2 to 11 random chars to end of table_name
        #  attempts 1:-3 datatable_xx, datatable_xxx, datatable_xxxx where x is random char
        #
        random_chars = get_random_chars(x+1)
        unique_vname = '%s_%s' % (view_name, random_chars)
    # ------------------------------------------------
    # Failed to generate a unique name, throw an error
    # ------------------------------------------------
    err_msg = """Failed to generate unique view name for the new Table Join.
Original: %s
Attempts: %s""" % (view_name, ', '.join(attempts))
    raise ValueError(err_msg)
