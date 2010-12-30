DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = 'geonode'
DATABASE_USER = 'geonode'             # Not used with sqlite3.
DATABASE_PASSWORD = 'geonode'         # Not used with sqlite3.
DATABASE_HOST = ''             # Not used with sqlite3.
DATABASE_PORT = ''             # Not used with sqlite3.

CELERY_RESULT_BACKEND = "database"
CELERY_RESULT_DBURI = "postgresql://geonode:geonode@localhost/geonode"
CELERYD_LOG_LEVEL = "DEBUG"
#CELERY_ALWAYS_EAGER = True
#CELERY_SEND_EVENTS = True
