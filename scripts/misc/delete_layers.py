#!/usr/bin/env python
from geonode.settings import GEONODE_APPS
import geonode.settings as settings

from geonode.geoserver.helpers import ogc_server_settings
from geonode.layers.models import Layer
from geonode.layers.models import Style
from geoserver.catalog import Catalog
import argparse
import os
from os.path import dirname, abspath
import psycopg2

import logging
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")

logger = logging.getLogger()
LOG_LEVEL = logging.INFO
FILE_LOG_LEVEL = logging.DEBUG

def setup_logging():
    logger.setLevel(LOG_LEVEL)
    formatter = logging.Formatter('[%(asctime)s] %(filename)s \
(%(levelname)s,%(lineno)d)\t: %(message)s')

    # Setup file logging
    filename = __file__.split('/')[-1]
    LOG_FILE_NAME = os.path.splitext(
        filename)[0] + '_' + time.strftime('%Y-%m-%d') + '.log'
    LOG_FOLDER = dirname(abspath(__file__)) + '/logs/'

    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)

    LOG_FILE = LOG_FOLDER + LOG_FILE_NAME
    fh = logging.FileHandler(LOG_FILE, mode='w')
    fh.setLevel(FILE_LOG_LEVEL)
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def delete_layer(keyword, layer_list):

    setup_logging()

    if keyword == 'all':
        layers = Layer.objects.all()
    else:
        if layer_list is None:
            layers = Layer.objects.filter(name__icontains=keyword)
        else:
            layers = []
            for l in layer_list:
                try:
                    layers.append(Layer.objects.get(name=l))
                except:
                    logging.error('No layer %s', l)

    logging.info('LAYERS: %s', layers)
    # print 'LAYERS ', layers

    total = len(layers)
    print 'TOTAL', total
    logging.info('TOTAL: %s', total)
    count = 1

    for layer in layers:

        print '#' * 40
        print 'LAYER ', layer.name
        logging.info('LAYER %s', layer.name)

        try:
            print 'Deleting Layer ... '
            logging.info('Deleting Layer ... ')
            layer.delete()
        except Exception:
            print 'Cannot delete geonode layer'
            logging.exception('Cannot delete geonode layer')
            pass
        print '#' * 40


def parse_arguments():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Enter keyword as layer name filter \
        eg _fh for FHM, sar_ for SAR, etc')
    parser.add_argument(
        'type', choices=['sar', 'dem', 'fhm', 'all'], action='append',
        help='Delete all layers in a specific layer type \
                        or delete all 3 layer type')
    parser.add_argument('--layer', nargs='+',
                        help='delete a specific layer or list of layers')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_arguments()
    for argType in args.type:
        if argType == 'fhm':
            keyword = '_fh'
            delete_layer(keyword, args.layer)
        elif argType == 'sar':
            keyword = 'sar_'
            delete_layer(keyword, args.layer)
        elif argType == 'dem':
            keyword = 'dem_'
            delete_layer(keyword, args.layer)
        elif argType == 'all':
            keyword = 'all'
            delete_layer(keyword, args.layer)
        else:
            print 'NO KEYWORD SUPPLIED. EXITING...'
