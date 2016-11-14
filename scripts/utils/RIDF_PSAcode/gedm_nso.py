from geonode.settings import GEONODE_APPS
import os
from osgeo import ogr
import shapely
from shapely.wkb import loads
import math
import geonode.settings as settings
from geonode.layers.models import Layer
import psycopg2

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")

# open db with ogr and connect to postgis
if "lipad" not in settings.BASEURL:
    source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format
                       (settings.HOST_ADDR, settings.GIS_DATABASE_NAME,
                        settings.DATABASE_USER, settings.DATABASE_PASSWORD)))
    conn = psycopg2.connect(("host={0} dbname={1} user={2} password={3}".format
                             (settings.HOST_ADDR, settings.GIS_DATABASE_NAME,
                              settings.DATABASE_USER, settings.DATABASE_PASSWORD)))
else:
    source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format
                       (settings.DATABASE_HOST, settings.DATASTORE_DB,
                        settings.DATABASE_USER, settings.DATABASE_PASSWORD)))
    conn = psycopg2.connect(("host={0} dbname={1} user={2} password={3}".format
                             (settings.DATABASE_HOST, settings.DATASTORE_DB,
                              settings.DATABASE_USER, settings.DATABASE_PASSWORD)))

cur = conn.cursor()

def postgis_layer():
    gadm_layer = source.GetLayer('gadm_municipal')
    nso_layer = source.GetLayer('nso_muni')


if __name__ == '__main__':
    # connect_to_postgis()
    postgis_layer()
