#!/usr/bin/env python

# SUC, floodplain tagging for PL1 layers
# RB tagging for DREAM layers
from geonode.settings import GEONODE_APPS
import geonode.settings as settings

from geonode.layers.models import Layer
import logging
import multiprocessing
import os
import psycopg2
import sys
import psycopg2.extras
from django.db.models import Q


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")

_logger = logging.getLogger()
_LOG_LEVEL = logging.DEBUG
_CONS_LOG_LEVEL = logging.DEBUG
_FILE_LOG_LEVEL = logging.DEBUG


def assign_tags(mode, results, layer):

    has_changes = False
    keywords = layer.keywords.names()
    fp_tags = layer.floodplain_tag.names()
    suc_tags = layer.SUC_tag.names()

    for r in results:
        if mode == 'dem':
            # Riverbasin
            if len(keywords) == 0 or r['rb_name'] not in keywords:
                _logger.info('%s: %s: Adding keyword: %s',
                             layer.name, mode, r['rb_name'])
                layer.keywords.add(r['rb_name'])
                has_changes = True
            if len(fp_tags) == 0 or r['rb_name'] not in fp_tags:
                _logger.info('%s: %s: Adding FP tag: %s',
                             layer.name, mode, r['rb_name'])
                layer.floodplain_tag.add(r['rb_name'])
                has_changes = True
        elif mode == 'fhm':
            # Floodplain - SUC
            if len(keywords) == 0 or r['Floodplain'] not in keywords:
                _logger.info('%s: %s: Adding keyword: %s',
                             layer.name, mode, r['Floodplain'])
                layer.keywords.add(r['Floodplain'])
                has_changes = True
            if len(keywords) == 0 or r['SUC'] not in keywords:
                _logger.info('%s: %s: Adding keyword: %s', layer.name, mode,
                             r['SUC'])
                layer.keywords.add(r['SUC'])
                has_changes = True
            if len(fp_tags) == 0 or r['Floodplain'] not in fp_tags:
                _logger.info('%s: %s: Adding FP tag: %s',
                             layer.name, mode, r['Floodplain'])
                layer.floodplain_tag.add(r['Floodplain'])
                has_changes = True
            if len(suc_tags) == 0 or r['SUC'] not in suc_tags:
                _logger.info('%s: %s: Adding SUC tag: %s', layer.name, mode,
                             r['SUC'])
                layer.SUC_tag.add(r['SUC'])
                has_changes = True
        elif mode == 'sar':
            # SUC
            if len(keywords) == 0 or r['SUC'] not in keywords:
                _logger.info('%s: %s: Adding keyword: %s', layer.name, mode,
                             r['SUC'])
                layer.keywords.add(r['SUC'])
                has_changes = True
            if len(keywords) == 0 or r['SUC'] not in suc_tags:
                _logger.info('%s: %s: Adding SUC tag: %s', layer.name, mode,
                             r['SUC'])
                layer.SUC_tag.add(r['SUC'])
                has_changes = True

    _logger.info('%s: Keywords: %s', layer.name, layer.keywords.names())
    _logger.info('%s: Floodplain Tags: %s', layer.name,
                 layer.floodplain_tag.names())
    _logger.info('%s: SUC Tags: %s', layer.name, layer.SUC_tag.names())

    return has_changes


def tag_layer(layers, mode):

    # Connect to database
    conn = psycopg2.connect(("host={0} dbname={1} user={2} password={3}".format
                             (settings.DATABASE_HOST,
                              settings.DATASTORE_DB,
                              settings.DATABASE_USER,
                              settings.DATABASE_PASSWORD)))

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    has_changes = False
    has_results = False
    deln = ''

    # for mode, deln in [('dem', settings.RB_DELINEATION_DREAM),
    #                    ('sar', settings.PL1_SUC_MUNIS),
    #                    ('fhm', settings.FHM_COVERAGE)]:
    for layer in layers:
        _logger.info('Layer name: %s', layer.name)

        # Construct query
        query = '''
WITH l AS (
    SELECT ST_Multi(ST_Union(f.the_geom)) AS the_geom
    FROM ''' + layer.name + ''' AS f
)'''

        if mode == 'dem':
            deln = settings.RB_DELINEATION_DREAM
            query += '''
SELECT d.rb_name FROM ''' + deln + ''' AS d, l '''
        elif mode == 'sar':
            deln = settings.PL1_SUC_MUNIS
            query += '''
SELECT DISTINCT d."SUC" FROM ''' + deln + ''' AS d, l'''
        elif mode == 'fhm':
            deln = settings.FHM_COVERAGE
            query += '''
SELECT d."Floodplain", d."SUC" FROM ''' + deln + ''' AS d, l'''
#         query += '''
# FROM ''' + deln + ''' AS d, l'''

        _logger.info('%s: mode: %s deln: %s', layer.name, mode, deln)
        # Get intersect
        query_int = (query + '''
 WHERE ST_Intersects(d.the_geom, l.the_geom);''')

        # Execute query
        try:
            _logger.info('%s query_int: %s', layer.name, query_int)
            cur.execute(query_int)
        except Exception:
            _logger.exception('%s: Error executing query_int!', layer.name)
            conn.rollback()
            # Skip layer
            continue

        # Get all results
        results = cur.fetchall()
        _logger.info('%s: results: %s', layer.name, results)

        # Get no. of results
        if len(results) >= 1:
            has_results = True
            if mode == 'sar':
                # tag SAR DEMs
                rem_extents = layer.name.split('_extents')[0]
                sar_layer = Layer.objects.get(name=rem_extents)
                if sar_layer is not None:
                    hc = assign_tags(mode, results, sar_layer)
                else:
                    _logger.info('DOES NOT EXIST %s', sar_layer.name)
                # tag SAR extents
                hc = assign_tags(mode, results, layer)
            else:
                hc = assign_tags(mode, results, layer)
            if hc:
                has_changes = True

    if not has_results:
        _logger.info('NO INTERSECTION %s', layer.name)

    if has_changes:
        try:
            _logger.info('%s: Saving layer...', layer.name)
            layer.save()
        except Exception:
            _logger.exception('%s: ERROR SAVING LAYER', layer.name)


def caller_function(keyword_filter):

    # Setup logging
    _logger.setLevel(_LOG_LEVEL)
    formatter = logging.Formatter(
        '[%(asctime)s] (%(levelname)s) : %(message)s')

    # Setup console logging
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(_CONS_LOG_LEVEL)
    ch.setFormatter(formatter)
    _logger.addHandler(ch)

    # Setup file logging
    # fh = logging.FileHandler(os.path.splitext(
    #     os.path.basename(__file__))[0] + '.log', mode='w')
    # fh.setLevel(_FILE_LOG_LEVEL)
    # fh.setFormatter(formatter)
    # _logger.addHandler(fh)

    # Initialize pool
    # pool = multiprocessing.Pool()
    # pool.map_async(tag_layer, layers)
    # pool.close()
    # pool.join()
    layers = ''
    if keyword_filter == 'sar':
        layers = Layer.objects.filter(Q(workspace='geonode') & Q(
            name__icontains=keyword_filter) &
            Q(name__icontains='_extents')).exclude(owner__username='dataRegistrationUploader')
    elif keyword_filter == 'dem':
        layers = Layer.objects.filter(Q(workspace='geonode') & Q(
            name__icontains=keyword_filter)).exclude(owner__username='dataRegistrationUploader')
    elif keyword_filter == 'fhm':
        layers = Layer.objects.filter(Q(workspace='geonode') & Q(
            name__icontains='_fh')).exclude(owner__username='dataRegistrationUploader')

    # for layer in layers:
    tag_layer(layers, keyword_filter)
