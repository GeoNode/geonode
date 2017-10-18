#!/usr/bin/env python

from geonode.settings import GEONODE_APPS
import geonode.settings as settings

import subprocess
import ogr
import os
import shutil
import time
import math
import argparse
import sys
import logging

from geonode.cephgeo.models import CephDataObject, LidarCoverageBlock

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")

_version = "0.3.2"
print os.path.basename(__file__) + ": v" + _version
_logger = logging.getLogger()
_LOG_LEVEL = logging.DEBUG
_CONS_LOG_LEVEL = logging.INFO
_FILE_LOG_LEVEL = logging.DEBUG

driver = ogr.GetDriverByName('ESRI Shapefile')


def get_cwd():
    cur_path = os.path.realpath(__file__)
    if "?" in cur_path:
        return cur_path.rpartition("?")[0].rpartition(os.path.sep)[0] + os.path.sep
    else:
        return cur_path.rpartition(os.path.sep)[0] + os.path.sep


def _setup_logging(args):
    # Setup logging`
    formatter = logging.Formatter("[%(asctime)s] %(filename)s \
(%(levelname)s,%(lineno)d) : %(message)s")

    # Check verbosity for console
    if args.verbose and args.verbose >= 1:
        global _CONS_LOG_LEVEL
        _CONS_LOG_LEVEL = logging.DEBUG

    # Setup console logging
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(_CONS_LOG_LEVEL)
    ch.setFormatter(formatter)
    _logger.addHandler(ch)

    # Setup file logging
    fh = logging.FileHandler(args.logfile)
    fh.setLevel(_FILE_LOG_LEVEL)
    fh.setFormatter(formatter)
    _logger.addHandler(fh)


def rename_laz(inDir, outDir, processor, block_name, block_uid):

    outDir = outDir.__add__('/' + block_name)
    print 'OutDir:', outDir
    if not os.path.exists(outDir):
        os.makedirs(outDir)

    # Loop through the input directory
    for path, dirs, files in os.walk(inDir, topdown=False):
        for laz in files:
            if laz.endswith(".laz"):  # or las.endswith(".las"):
                typeFile = laz.split(".")[-1].upper()
                ctr = 0
                laz_file_path = os.path.join(path, laz)

                # get LAZ bounding box/extents
                p = subprocess.Popen([os.path.join(get_cwd(), 'lasbb'), '-get_bb',
                                      laz_file_path], stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT)
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

                    # outFN =
                    # ''.join(['E',tile_x,'N',tile_y,'_',typeFile,'.',typeFile.lower()])
                    outFN = 'E{0}N{1}_{2}_{3}_U{4}.{5}'.format(
                        tile_x, tile_y, typeFile, processor, block_uid, typeFile.lower())
                    outPath = os.path.join(outDir, outFN)

                    # Check if output filename is already exists
                    while os.path.exists(outPath):
                        print '\nWARNING:', outPath, 'already exists!'
                        ctr += 1
                        # outFN =
                        # ''.join(['E',minX,'N',maxY,'_',typeFile,'_',str(ctr),'.',typeFile.lower()])
                        outFN = 'E{0}N{1}_{2}_{3}_U{4}_{5}.{6}'.format(
                            tile_x, tile_y, typeFile, processor, block_uid,
                            str(ctr), typeFile.lower())
                        # print outFN
                        outPath = os.path.join(outDir, outFN)

                    print os.path.join(path, laz), outFN

                    _logger.info(os.path.join(path, laz) +
                                 ' --------- ' + outFN + '\n')

                    print outPath, 'copied successfully'
                    shutil.copy(laz_file_path, outPath)
                else:
                    _logger.error("Error reading extents of [{0}]. Trace from \
                        lasbb:\n{1}".format(
                        laz_file_path, out))

    endTime = time.time()  # End timing
    print '\nElapsed Time:', str("{0:.2f}".format(round(endTime - startTime, 2))), 'seconds'


def find_in_coverage(block_name):
    try:
        # get block_name in LidarCoverageBlock Model
        block = LidarCoverageBlock.objects.get(block_name=block_name)
        print 'Block in Lidar Coverage'
        print 'Block UID:', block.uid
        return True, block.uid
    except Exception:
        print 'Block not in Lidar Coverage', block_name
        return False, 0


def proper_block_name(block_path):

    # input format: ../../Agno_Blk5C_20130418

    # parses blockname from path
    block_name = block_path.split(os.sep)[-1]
    if block_name == '':
        block_name = block_path.split(os.sep)[-2]
    # remove date flown
    block_name = block_name.rsplit('_', 1)[0]

    print 'BLOCK NAME', block_name
    return block_name


def assign_processor(processor):
    value = processor.lower()
    list_ = {'DRM': ['dream', 'drm', 'd'],
             'PL1': ['phil-lidar', 'pl', 'pl1']}
    for k, v in list_.items():
        if value in v:
            print 'Processor', k
            return k
    return None


def parse_arguments():
    parser = argparse.ArgumentParser(description='Rename LAZ Files')
    parser.add_argument("-v", "--verbose", action="count")
    # parser.add_argument('-i', '--input_directory')
    # parser.add_argument('-o', '--output_directory')
    # parser.add_argument('-t','--type')
    # parser.add_argument("-tmp", "--temp-dir", required=True,
    #                        help="Path to temporary working directory.")
    # parser.add_argument("-rbid", "--rbid", required=True,
    #                     help="River basin ID for this DEM.")
    parser.add_argument("-p", "--processor", required=True,
                        help="Processor for this LAZ (dream or phil-lidar)")
    parser.add_argument("-l", "--logfile", required=True,
                        help="Filename of logfile")

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_arguments()
    _setup_logging(args)
    # Start timing
    startTime = time.time()

    # inDir = args.input_directory
    # outDir = args.output_directory
    inDir = os.path.abspath(
        '/home/geonode/Work/Data/Copied_blocks/Agno/Agno_Blk5C_20130418/')
    outDir = '/home/geonode/Work/Data/Copied_blocks/Renamed/'
    # typeFile = args.type.upper()
    # fileExtn = args.type.lower()

    # if typeFile != "LAS" and typeFile != "LAZ":
    #   print typeFile, 'is not a supported format'
    #   sys.exit()

    block_name = proper_block_name(inDir)
    in_coverage, block_uid = find_in_coverage(block_name)
    if in_coverage:
        print 'Found in Lidar Coverage model', block_name, block_uid
        processor = assign_processor(args.processor)
        rename_laz(inDir, outDir, processor, block_name, block_uid)
    else:
        print 'ERROR NOT FOUND IN MODEL', block_name, block_uid
