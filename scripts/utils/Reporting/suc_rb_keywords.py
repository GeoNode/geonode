#!/usr/bin/env python

# SUC, floodplain tagging for PL1 layers

from geonode.settings import GEONODE_APPS
import geonode.settings as settings
import os
from geonode.layers.models import Layer
from geonode.cephgeo.models import RIDF
from pprint import pprint
from django.db.models import Q
import psycopg2
from osgeo import ogr
import traceback
import logging
import sys

_logger = logging.getLogger()
_LOG_LEVEL = logging.DEBUG
_CONS_LOG_LEVEL = logging.INFO
_FILE_LOG_LEVEL = logging.DEBUG

_logger.setLevel(_LOG_LEVEL)
formatter = logging.Formatter(
    '[%(asctime)s] (%(levelname)s) : %(message)s')

# Setup console logging
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(_CONS_LOG_LEVEL)
ch.setFormatter(formatter)
_logger.addHandler(ch)

# Setup file logging
fh = logging.FileHandler(os.path.splitext(
    os.path.basename(__file__))[0] + '.log', mode='w')
fh.setLevel(_FILE_LOG_LEVEL)
fh.setFormatter(formatter)
_logger.addHandler(fh)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")


source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format
                   (settings.HOST_ADDR, settings.GIS_DATABASE_NAME,
                    settings.DATABASE_USER, settings.DATABASE_PASSWORD)))
conn = psycopg2.connect(("host={0} dbname={1} user={2} password={3}".format
                         (settings.HOST_ADDR, settings.GIS_DATABASE_NAME,
                          settings.DATABASE_USER, settings.DATABASE_PASSWORD)))
cur = conn.cursor()
# layer = Layer.objects.get(name__icontains='jovellar_fh100yr_10m_1')
layers = Layer.objects.filter(name__icontains='_fh')
fp_delineation = settings.FP_DELINEATION
count = 1

for layer in layers:
    layer_name = layer.name
    _logger.info('{0} Layer name: {1}'.format(count, layer_name))
    query = '''
    WITH fhm AS (
        SELECT ST_Multi(ST_Union(f.the_geom)) AS the_geom 
        FROM ''' + layer_name + ''' AS f
    ) 
    SELECT a."FP_Name", a."SUC" 
    FROM ''' + fp_delineation + ''' AS a, fhm 
    WHERE ST_Contains(a.the_geom, ST_Centroid(fhm.the_geom)) 
          AND ST_Intersects(a.the_geom, fhm.the_geom);
    '''
    _logger.info('Query: %s', query)
    try:
        cur.execute(query)
    except psycopg2.ProgrammingError:
        _logger.exception('ERROR EXECUTING QUERY')
        # traceback.print_exc()
        conn.rollback()
        continue
    records = cur.fetchall()
    _logger.info('Records: %s', records)
    if len(records) > 1:
        _logger.error('RETURNED MORE THAN 1 FP-SUC PAIR: ', records)
    elif len(records) == 1:
        pair = {}
        pair['floodplain'] = records[0][0]
        pair['suc'] = records[0][1]
        _logger.info(
            'FP:{0} - SUC:{1}'.format(pair['floodplain'], pair['suc']))
        layer.keywords.add(pair['floodplain'])
        layer.keywords.add(pair['suc'])
        try:
            layer.save()
            _logger.debug('Keywords: {0}'.format(layer.keywords.values_list()))
        except:
            _logger.exception('ERROR SAVING LAYER')
    else:
        _logger.error('NO FP-SUC PAIR FOUND')
    count+=1
