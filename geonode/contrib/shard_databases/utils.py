import datetime
import logging
from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import dj_database_url

from django.conf import settings

from geonode.layers.models import Layer
from .models import Database


logger = logging.getLogger(__name__)


def get_shard_database_name():
    """
    Return the current PostGIS shard database name. It creates the database if it does not exist.
    """
    shard_strategy = getattr(settings, 'SHARD_STRATEGY', 'monthly')
    if shard_strategy not in ('monthly', 'yearly', 'layercount'):
        raise ValueError('SHARD_STRATEGY must be set to "monthly", "yearly" or "layercount"')
    shard_prefix = getattr(settings, 'SHARD_PREFIX', '')
    shard_suffix = getattr(settings, 'SHARD_SUFFIX', '')
    shard_layer_count = getattr(settings, 'SHARD_LAYER_COUNT', 100)
    if shard_strategy == 'monthly':
        db_name = '%s%s%s' % (shard_prefix, datetime.datetime.today().strftime('%Y%m'), shard_suffix)
        create_postgis_database(db_name, Database.MONTHLY)
    if shard_strategy == 'yearly':
        db_name = '%s%s%s' % (shard_prefix, datetime.datetime.today().strftime('%Y'), shard_suffix)
        create_postgis_database(db_name, Database.YEARLY)
    if shard_strategy == 'layercount':
        shard_numeric_code = Database.objects.filter(strategy_type=Database.LAYERCOUNT).count()
        if shard_numeric_code > 0:
            # Do we really need a new shard?
            last_store_name = Database.objects.filter(strategy_type=Database.LAYERCOUNT).order_by('-created_at')[0].name
            if Layer.objects.filter(store=last_store_name).count() <= shard_layer_count:
                shard_numeric_code -= 1
        db_name = '%s%05d%s' % (shard_prefix, shard_numeric_code, shard_suffix)
        if Database.objects.filter(name=db_name).count() == 0:
            create_postgis_database(db_name, Database.LAYERCOUNT)

    # update layers count (only needed for layercount strategy)
    if shard_strategy == 'layercount':
        shardatabase = Database.objects.get(name=db_name)
        shardatabase.layers_count = Layer.objects.filter(store=db_name).count()
        shardatabase.save()
    return db_name


def create_postgis_database(db_name, shard_strategy):
    """
    Create the PostGIS shard database name.
    """
    shardatabase, created = Database.objects.get_or_create(name=db_name, strategy_type=shard_strategy)
    if created:
        print 'We need to create the db now %s' % db_name
        logger.info("Creating a new PostGIS datatase: %s" % db_name)
        try:
            datastore_db = dj_database_url.parse(settings.DATASTORE_URL)
            user = datastore_db['USER']
            host = datastore_db['HOST']
            port = datastore_db['PORT']
            password = datastore_db['PASSWORD']
            # 1. create the database
            conn = connect(user=user, host=host, port=port, password=password)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute('CREATE DATABASE %s;' % db_name)
            cur.close()
            conn.close()
            # 2. enable PostGIS
            conn = connect(dbname=db_name, user=user, host=host, port=port, password=password)
            cur = conn.cursor()
            cur.execute('CREATE EXTENSION postgis;')
            cur.close()
            conn.commit()
            conn.close()
        except Exception as e:
            print str(e)
            logger.error(
                "Error creating PostGIS database shard %s: %s" % (db_name, str(e)))
        finally:
            try:
                if conn:
                    conn.close()
            except Exception as e:
                logger.error("Error closing PostGIS conn %s", str(e))
