#!/usr/bin/env python

from geonode.settings import GEONODE_APPS
import geonode.settings as settings

import traceback
from geonode.layers.models import Layer
from pprint import pprint
from geonode.cephgeo.models import CephDataObject, LidarCoverageBlock

import subprocess
import ogr
import os
import shutil
import time
import math
import argparse
import sys


# global block_name = ''


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")


def get_cwd():
    cur_path = os.path.realpath(__file__)
    if "?" in cur_path:
        return cur_path.rpartition("?")[0].rpartition(os.path.sep)[0] + os.path.sep
    else:
        return cur_path.rpartition(os.path.sep)[0] + os.path.sep


def rename_laz(inDir, outDir, processor):
    # inDir = assume Block folder
    if not os.path.exists(outDir):
        os.makedirs(outDir)

    for path, dirs, files in os.walk(inDir, topdown=False):
        for las in files:
            # if las.endswith(".laz") or las.endswith(".las"):
            if las.endswith(".laz"):
                typeFile = las.split(".")[-1].upper()
                ctr = 0
                laz_file_path = os.path.join(path, las)

                # get LAZ bounding box/extents
                p = subprocess.Popen([os.path.join(get_cwd(), 'lasbb'), '-get_bb',
                                      laz_file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out, err = p.communicate()
                returncode = p.returncode
                if returncode is 0:
                    tokens = out.split(" ")
                    minX = float(tokens[1])
                    minY = float(tokens[2])
                    maxX = float(tokens[3])
                    maxY = float(tokens[4])

                    bbox_center_x = (minX + (maxX - minX) / 2)
                    bbox_center_y = (minY + (maxY - minY) / 2)

                    _TILE_SIZE = 1000
                    tile_x = int(math.floor(bbox_center_x / float(_TILE_SIZE)))
                    tile_y = int(math.floor(
                        bbox_center_y / float(_TILE_SIZE))) + 1

                    #outFN = ''.join(['E',tile_x,'N',tile_y,'_',typeFile,'.',typeFile.lower()])

                    outFN = 'E{0}N{1}'.format(tile_x, tile_y)
                    # outPath = os.path.join(outDir,outFN)

                    print 'OUTPUT PATH ', outFN
                else:
                    print "Error reading extents of [{0}]. Trace from lasbb:\n{1}".format(laz_file_path, out)
        print 'TRAVERSAL FINISHED'


def block_name(block_path):
    # parses blockname from path
    # input format: ../../Agno_Blk5C_20130418

    block_name = block_path.split(os.sep)[-1]
    if block_name == '':
        block_name = block_path.split(os.sep)[-2]
    # remove date flown
    block_name = block_name.rsplit('_', 1)[0]

    print 'BLOCK NAME', block_name
    return block_name


def find_in_coverage(block_name):
    # find block_name in lidar coverage model
    try:
        block = LidarCoverageBlock.objects.get(block_name=block_name)
        print 'Block in Lidar Coverage'
        print 'Block UID:', block.uid
        return block.uid
    except Exception:
        print 'Block not in Lidar Coverage', block_name
        return 0


def get_ceph_object():
    pass

if __name__ == '__main__':
    block_name = ''

    print 'PATH.BASENAME ', os.path.basename(__file__)
    print 'PATH.JOIN GETCWD LASBB ', os.path.join(get_cwd(), 'lasbb')
    # LAZ folder path
    # blk_path_agno5A = '/home/geonode/DATA/LAS_FILES'

    blk_path = '/home/geonode/DATA/Adjusted_LAZ_Tiles/DREAM/Agno/Agno5C_20130418'
    # blk_name = block_name(blk_path)
    outDir = '/home/geonode/DATA/Output/'
    print 'Rename Laz'
    # rename_laz(blk_path, outDir)

    inDir = os.path.abspath(
        '/home/geonode/Work/Data/Renamed/Agno/Agno_Blk5C_20130418')
    if not os.path.isdir(inDir):
        print 'Input directory error!'

    # data processor is DREAM or Phil-lidar
    processor = 'DRM' #,'PL1'
    # walk through all .laz
    rename_laz(inDir, outDir, processor)

    for path, dirs, files in os.walk(inDir, topdown=False):
        block_name = block_name(path)
        block_uid = find_in_coverage(block_name)
        if block_uid > 0:
            # parse laz files
            for laz in files:
                if laz.endswith('.laz'):
                    print 'LAZ filename:', laz
                    # parse gridref from filename
                    # filename: Gridref_datatype_etc..
                    gridref = laz.split('.')[0].split('_')[0]
                    print 'Gridref:', gridref
        else:
            # write in logfile
            print 'Write ' + block_name + ' in log file'
