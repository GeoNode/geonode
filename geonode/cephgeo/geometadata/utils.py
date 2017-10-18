from geonode.settings import GEONODE_APPS
import geonode.settings as settings

from geonode.cephgeo.models import LidarCoverageBlock, CephDataObject

import os
from osgeo import ogr
import shapely
from shapely.wkb import loads
import math
import geonode.settings as settings
from collections import defaultdict
import json
from shapely.geometry import Polygon
# import datetime
from datetime import datetime, timedelta
from unidecode import unidecode
import traceback
from geonode.cephgeo import client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")

# save Lidar coverage to model


def create_object(params):
    obj = LidarCoverageBlock.objects.create(uid=params['uid'],
                                            block_name=params['block_name'],
                                            adjusted_l=params['adjusted_l'],
                                            sensor=params['sensor'],
                                            processor=params['processor'],
                                            flight_num=params['flight_num'],
                                            mission_na=params['mission_na'],
                                            date_flown=params['date_flown'],
                                            x_shift_m=params['x_shift_m'],
                                            y_shift_m=params['y_shift_m'],
                                            z_shift_m=params['z_shift_m'],
                                            height_dif=params['height_dif'],
                                            rmse_val_m=params['rmse_val_m'],
                                            cal_ref_pt=params['cal_ref_pt'],
                                            val_ref_pt=params['val_ref_pt'],
                                            floodplain=params['floodplain'],
                                            pl1_suc=params['pl1_suc'],
                                            pl2_suc=params['pl2_suc'])
    return obj


def lidar_coverage_data():
    source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(
        settings.DATABASE_HOST, settings.GIS_DATABASE_NAME, settings.DATABASE_USER, settings.DATABASE_PASSWORD)))

    layer = source.GetLayer(settings.LIDAR_COVERAGE)
    print 'Lidar Coverage layer name:', layer.GetName()

    i = 0
    feature_count = layer.GetFeatureCount()
    # print '', feature_count, ' Features'
    for feature in layer:
        i += 1
        params = {}
        params['uid'] = feature.GetFieldAsInteger('uid')
        params['block_name'] = feature.GetFieldAsString('block_name')
        params['adjusted_l'] = feature.GetFieldAsString('adjusted_l')
        params['sensor'] = feature.GetFieldAsString('sensor')
        params['processor'] = feature.GetFieldAsString('processor')
        params['flight_num'] = feature.GetFieldAsString('flight_num')
        params['mission_na'] = feature.GetFieldAsString('mission_na')
        temp = feature.GetFieldAsString('date_flown')
        if temp != '':
            print 'Temp', temp
            temp_date = datetime.strptime(
                temp, "%Y/%m/%d %H:%M:%S") + timedelta(hours=8)
            print 'Temp date', temp_date
            params['date_flown'] = datetime(
                temp_date.year, temp_date.month, temp_date.day)
        else:
            params['date_flown'] = None
        params['x_shift_m'] = feature.GetFieldAsString('x_shift_m')
        params['y_shift_m'] = feature.GetFieldAsString('y_shift_m')
        params['z_shift_m'] = feature.GetFieldAsString('z_shift_m')
        params['height_dif'] = feature.GetFieldAsString('height_dif')
        params['rmse_val_m'] = feature.GetFieldAsString('rmse_val_m')
        params['cal_ref_pt'] = feature.GetFieldAsString('cal_ref_pt')
        params['val_ref_pt'] = feature.GetFieldAsString('val_ref_pt')
        params['floodplain'] = feature.GetFieldAsString('floodplain')
        params['pl1_suc'] = feature.GetFieldAsString('pl1_suc')
        params['pl2_suc'] = feature.GetFieldAsString('pl2_suc')

        # print params
        print 'Creating object...'
        try:
            obj = create_object(params)
            print '#' * 40
            print i, '/', feature_count
            print 'UID:', obj.uid
            print 'block_name:', obj.block_name
            print 'adjusted_l:', obj.adjusted_l
            print 'sensor:', obj.sensor
            print 'processor:', obj.processor
            print 'flight_num:', obj.flight_num
            print 'mission_na:', obj.mission_na
            print 'date_flown:', obj.date_flown
        except Exception:
            print 'Error creating object!'
            traceback.print_exc()
        # break

# Make button for this
# Dont forget to include update workflow
# lidar_coverage_data()
# print 'Finished all blocks'

def existence_in_cephstorage(renamed_block_path=None):
    # input folder is parent folder
    # walk through renamed laz files
    # delete files with overlap in ceph storage , lipad
    if inDir is None:
        inDir = '/home/geonode/Work/Data/Renamed/Agno_Blk5C/'

    cephclient = client.CephStorageClient(settings.CEPH_OGW['default']['USER'],
                                          settings.CEPH_OGW['default']['KEY'],
                                          settings.CEPH_OGW['default']['LOCATION'])

    # check same filename
    for path, dirs, files in os.walk(inDir, topdown=False):
        for laz in files:
            if cephclient.does_exist(laz):
                # delete ceph storage object

                # delete ceph data object
                try:
                    ceph_obj = CephDataObject.objects.get(name=laz)
                    print 'Deleting ceph data object',  ceph_obj.name
                    # ceph_obj.delete()
                except Exception:
                    print 'No Ceph Data Object in Model', ceph_obj.name

            else:
                print 'Uploading to Ceph Storage', laz
                cephclient.bulk_upload_nonthreaded(laz)

                print 'Creating Ceph Data Object for', laz
                CephDataObject.objects.create()
