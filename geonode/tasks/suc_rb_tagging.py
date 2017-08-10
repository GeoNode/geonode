import geonode.settings as settings

from celery.utils.log import get_task_logger
from geonode.layers.models import Layer
import logging
import psycopg2

logger = get_task_logger("geonode.tasks.update")
logger.setLevel(logging.INFO)


def assign_tag(mode, records, layer):
    if mode == 'dream':
        _dict = {}
        _dict['floodplain'] = records[0][0]
        logger.info(
            'FP:{0}'.format(_dict['floodplain']))
        layer.keywords.add(_dict['floodplain'])
        layer.floodplain_tag.add(_dict['floodplain'])
        try:
            layer.save()
            logger.debug('Keywords: {0}'.format(
                layer.keywords.values_list()))
            logger.debug('Floodplain Tag: {0}'.format(
                layer.floodplain_tag.values_list()))
        except:
            logger.exception('ERROR SAVING LAYER')
    else:
        pair = {}
        pair['floodplain'] = records[0][0]
        pair['suc'] = records[0][1]
        logger.info(
            'FP:{0} - SUC:{1}'.format(pair['floodplain'], pair['suc']))
        layer.keywords.add(pair['floodplain'])
        layer.keywords.add(pair['suc'])
        layer.floodplain_tag.add(pair['floodplain'])
        layer.SUC_tag.add(pair['suc'])
        try:
            layer.save()
            logger.debug('Keywords: {0}'.format(
                layer.keywords.values_list()))
            logger.debug('Floodplain Tag: {0}'.format(
                layer.floodplain_tag.values_list()))
            logger.debug('SUC Tag: {0}'.format(
                layer.SUC_tag.values_list()))
        except:
            logger.exception('ERROR SAVING LAYER')


def tag_layers(mode, delineation, cur, conn, source):
    count = 1
    layers = Layer.objects.filter(name__icontains='_fh')
    total = len(layers)
    for layer in layers:
        layer_name = layer.name
        if mode == 'dream':
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

        logger.info(
            '{0}/{2} Layer name: {1}'.format(count, layer_name, total))
        logger.info('Query: %s', query)
        try:
            cur.execute(query)
        except psycopg2.ProgrammingError:
            logger.exception('ERROR EXECUTING QUERY')
            # traceback.print_exc()
            conn.rollback()
            continue
        records = cur.fetchall()
        logger.info('Records: %s', records)
        if len(records) > 1:
            if mode == 'dream':
                logger.error('RETURNED MORE THAN 1 FP: %s', records)
            else:
                logger.error('RETURNED MORE THAN 1 FP-SUC PAIR: %s ', records)
        elif len(records) == 1:
            assign_tag(mode, records, layer)
        else:
            if mode == 'dream':
                logger.error('RETURNED 0 FP: %s', records)
            else:
                logger.error('RETURNED 0 FP-SUC PAIR: %s', records)
        count += 1
