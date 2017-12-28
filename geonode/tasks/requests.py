import sys
import traceback
from pprint import pprint
from celery.task import task
from django.core.mail import send_mail

import psycopg2
import psycopg2.extras
import sys

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
    message = "The following data requests have been tagged:\n\n"
    for dr in data_requests:
        if dr.jurisdiction_shapefile:
            sucs = get_sucs(dr.jurisdiction_shapefile)
            flatten_sucs = [s for suc in sucs for s in suc]
            dr.suc.clear()
            for s in flatten_sucs:
                dr.suc.add(s)
            message += settings.SITEURL + str(dr.get_absolute_url().replace('//','/')) + "\n"
    subject = "SUC tagging done"
    recipient = [settings.LIPAD_SUPPORT_MAIL]
    send_mail(subject, message, settings.LIPAD_SUPPORT_MAIL, recipient, fail_silently= False)

####utility functions

def get_sucs(layer, sucs_layer=settings.PL1_SUC_MUNIS, proj=32651):
    conn = psycopg2.connect(("host={0} dbname={1} user={2} password={3}".format
                             (settings.DATABASE_HOST,
                              settings.DATASTORE_DB,
                              settings.DATABASE_USER,
                              settings.DATABASE_PASSWORD)))

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = '''
    WITH l AS (
        SELECT ST_Multi(ST_Transform(ST_Union(f.the_geom), '''+str(proj)+''')) AS the_geom
        FROM ''' + layer.name + ''' AS f
    ) SELECT DISTINCT d."SUC" FROM ''' + sucs_layer + ''' AS d, l WHERE ST_Intersects(d.the_geom, l.the_geom);'''

    try:
        cur.execute(query)
    except Exception:
        print traceback.format_exc()
        conn.rollback()
        return []
    result = cur.fetchall()
    pprint(len(result))
    return result
