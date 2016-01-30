from django.conf import settings
from collections import OrderedDict

DB_PARAM_NAMES = ['NAME', 'USER', 'PASSWORD', 'PORT','HOST']

CHOSEN_DB_SETTING = 'wmdata'

# psql -d wmdata -U wmuser -W

def get_datastore_connection_string(url_format=False):
    """
    Create a connection string to access the database directly
    
    Use: settings.DATABASES[CHOSEN_DB_SETTING]
    
    e.g. "dbname='wmdb' user='username' password='the-pw' port=123 host=db.hostname.edu"
    """
    global DB_PARAM_NAMES, CHOSEN_DB_SETTING
    assert hasattr(settings, 'DATABASES'), "settings.DATABASES attribute not found in the settings file."
    assert settings.DATABASES.has_key(CHOSEN_DB_SETTING)\
                    , "settings.DATABASES does not have a '%s' key.  Please check your settings file." % CHOSEN_DB_SETTING

    db_params = settings.DATABASES[CHOSEN_DB_SETTING] 

    for attr in DB_PARAM_NAMES:
        assert db_params.has_key(attr), "Check your settings file. DATABASES['default'] does not specify a '%s'" % attr
        
    
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