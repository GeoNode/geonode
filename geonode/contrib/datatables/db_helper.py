from django.conf import settings
from collections import OrderedDict

from geonode.maps import utils

DB_PARAM_NAMES = ['NAME', 'USER', 'PASSWORD', 'PORT','HOST']

CHOSEN_DB_SETTING = 'wmdata'
DATAVERSE_DB = settings.DB_DATAVERSE_NAME

# psql -d wmdata -U wmuser -W

def get_database_name(is_dataverse_db):
    """
    Determine database to use.
    """
    if is_dataverse_db:
        return DATAVERSE_DB
    else:
        return utils.get_db_store_name()


def get_datastore_connection_string(url_format=False, is_dataverse_db=True, db_name=None):
    """
    Create a connection string to access the database directly

    Use: settings.DATABASES[CHOSEN_DB_SETTING]

    e.g. "dbname='wmdb' user='username' password='the-pw' port=123 host=db.hostname.edu"
    """
    global DB_PARAM_NAMES, CHOSEN_DB_SETTING

    db_params = settings.DATABASES[CHOSEN_DB_SETTING]

    for attr in DB_PARAM_NAMES:
        assert db_params.has_key(attr), "Check your settings file. DATABASES['default'] does not specify a '%s'" % attr


    # if in production, we rewrite db_param['NAME'] depending on a few situations
    # for datatables, target join layers and joins db is always the same
    #if not settings.DEBUG:
    if db_name:
        db_params['NAME'] = db_name
    else:
        db_params['NAME'] = get_database_name(is_dataverse_db)

    if url_format:
        # connection_string = "postgresql://%s:%s@%s:%s/%s" % (db['USER'], db['PASSWORD'], db['HOST'], db['PORT'], db['NAME'])
        conn_str = "postgresql://%s:%s@%s:%s/%s" % \
                        (db_params['USER'], db_params['PASSWORD'], db_params['HOST'], db_params['PORT'], db_params['NAME'])
    else:
        conn_str = """dbname='%s' user='%s' password='%s' port=%s host='%s'""" % \
                    tuple([db_params.get(x) for x in DB_PARAM_NAMES])



    #print 'conn_str', conn_str
    return conn_str

    '''
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
    "'"
    '''
