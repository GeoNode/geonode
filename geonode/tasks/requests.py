import sys
import traceback
from pprint import pprint
from celery.task import task

import psycopg2
import sys
import psycopg2.extras

import geonode.settings as settings
from geonode.datarequests.models import (
    ProfileRequest, DataRequest, DataRequestProfile, SUC_Contact)

@task(name="geonode.tasks.requests.set_status_for_multiple_requests",queue='requests')
def set_status_for_multiple_requests(requests, status, administrator=None):
    for r in requests:
        r.set_status(status, administrator)
    
@task(name="geonode.tasks.requests.migrate_all",queue='requests')
def migrate_all():
    old_requests = DataRequestProfile.objects.all()
    count = 0
    for r in old_requests:
        pprint("Migratig DataRequestProfile ID# "+str(r.pk))
        profile_request = r.migrate_request_profile()
        if profile_request:
            data_request = r.migrate_request_data()
            
            
@task(name="geonode.tasks.requests.tag_request_suc",queue='requests')
def tag_request_suc(data_requests):
    for dr in data_requests:
        if dr.jurisdiction_shapefile:
            sucs = get_sucs(jurisdiction_shapefile)
            pprint(sucs)
        
        
        
def get_sucs(layer, sucs_layer=settings.PL1_SUC_MUNIS):
    conn = psycopg2.connect(("host={0} dbname={1} user={2} password={3}".format
                             (settings.DATABASE_HOST,
                              settings.DATASTORE_DB,
                              settings.DATABASE_USER,
                              settings.DATABASE_PASSWORD)))

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    query = '''
    WITH l AS (
        SELECT ST_Multi(ST_Union(f.the_geom)) AS the_geom
        FROM ''' + layer.name + ''' AS f
    ) SELECT DISTINCT d."SUC" FROM ''' + sucs_layer + ''' AS d, l WHERE ST_Intersects(d.the_geom, l.the_geom);'''
    
    try:
        _logger.info('%s query_int: %s', layer.name, query_int)
        cur.execute(query_int)
    except Exception:
        print traceback.format_exc()
        conn.rollback()
        return []
        
    return results = cur.fetchall()
