#!/usr/bin/env python

# SUC, floodplain tagging for PL1 layers
# RB tagging for DREAM layers
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

def assign_tag(mode,records,layer):
    if mode=='dream':
        _dict = {}
        _dict['floodplain'] = records[0][0]
        _logger.info(
            'FP:{0}'.format(_dict['floodplain']))
        layer.keywords.add(_dict['floodplain'])
        layer.floodplain_tag.add(_dict['floodplain'])
        try:
            layer.save()
            _logger.debug('Keywords: {0}'.format(
                layer.keywords.values_list()))
            _logger.debug('Floodplain Tag: {0}'.format(
                layer.floodplain_tag.values_list()))
        except:
            _logger.exception('ERROR SAVING LAYER')
    else:
        pair = {}
        pair['floodplain'] = records[0][0]
        pair['suc'] = records[0][1]
        _logger.info(
            'FP:{0} - SUC:{1}'.format(pair['floodplain'], pair['suc']))
        layer.keywords.add(pair['floodplain'])
        layer.keywords.add(pair['suc'])
        layer.floodplain_tag.add(pair['floodplain'])
        layer.SUC_tag.add(pair['suc'])
        try:
            layer.save()
            _logger.debug('Keywords: {0}'.format(
                layer.keywords.values_list()))
            _logger.debug('Floodplain Tag: {0}'.format(
                layer.floodplain_tag.values_list()))
            _logger.debug('SUC Tag: {0}'.format(
                layer.SUC_tag.values_list()))
        except:
            _logger.exception('ERROR SAVING LAYER')

def tag_layers(mode,delineation):
    count = 1
    layers = Layer.objects.filter(name__icontains='_fh')
    total = len(layers)
    for layer in layers:
        layer_name = layer.name
        if mode=='dream':
            query = '''
                WITH fhm AS (
                    SELECT ST_Multi(ST_Union(f.the_geom)) AS the_geom 
                    FROM ''' + layer_name + ''' AS f
                ) 
                SELECT a.rb_name 
                FROM ''' + delineation + ''' AS a, fhm 
                WHERE ST_Contains(a.the_geom, ST_Centroid(fhm.the_geom)) 
                      AND ST_Intersects(a.the_geom, fhm.the_geom);
                '''
        else:
            query = '''
                WITH fhm AS (
                    SELECT ST_Multi(ST_Union(f.the_geom)) AS the_geom 
                    FROM ''' + layer_name + ''' AS f
                ) 
                SELECT a."FP_Name", a."SUC" 
                FROM ''' + delineation + ''' AS a, fhm 
                WHERE ST_Contains(a.the_geom, ST_Centroid(fhm.the_geom)) 
                      AND ST_Intersects(a.the_geom, fhm.the_geom);
                '''

        _logger.info('{0}/{2} Layer name: {1}'.format(count, layer_name,total))
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
            if mode=='dream':
                _logger.error('RETURNED MORE THAN 1 FP: %s', records)
            else:
                _logger.error('RETURNED MORE THAN 1 FP-SUC PAIR: '%s, records)
        elif len(records) == 1:
            assign_tag(mode,records,layer)
        else:
            if mode=='dream':
                _logger.error('RETURNED 0 FP: %s', records)
            else:
                _logger.error('RETURNED 0 FP-SUC PAIR: %s', records)
        count += 1

_logger.info('################################################')
_logger.info('DREAM LAYERS')
_logger.info('################################################')
tag_layers('dream',settings.RB_DELINEATION_DREAM)
_logger.info('################################################')
_logger.info('DREAM LAYERS TAGGING DONE')
_logger.info('################################################')

_logger.info('################################################')
_logger.info('PHIL-LIDAR 1 LAYERS')
_logger.info('################################################')
tag_layers('',settings.FP_DELINEATION_PL1)
_logger.info('################################################')
_logger.info('PHIL-LIDAR 1 LAYERS TAGGING DONE')
_logger.info('################################################')