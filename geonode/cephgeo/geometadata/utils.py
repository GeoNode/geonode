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
    obj, created = LidarCoverageBlock.objects.get_or_create(uid=params['uid'])
    obj.area=params['area'],
    obj.block_name=params['block_name']
    obj.processor=params['processor']
    obj.sensor=params['sensor']
    obj.base_used=params['base_used']
    obj.flight_num=params['flight_num']
    obj.mission_na=params['mission_na']
    obj.date_flown=params['date_flown']
    obj.x_shift=params['x_shift']
    obj.y_shift=params['y_shift']
    obj.z_shift=params['z_shift']
    obj.height_dif=params['height_dif']
    obj.rmse_val=params['rmse_val']
    obj.cal_ref_pt=params['cal_ref_pt']
    obj.val_ref_pt=params['val_ref_pt']
    obj.floodplain=params['floodplain']
    obj.pl1_suc=params['pl1_suc']
    obj.pl2_suc=params['pl2_suc']
    obj.is_laz_adj=params[]'is_adjuste']
    # obj.is_laz_adj=params['is_laz_adj']
    # obj.is_orp_adj=params['is_orp_adj']
    # obj.is_laz_upl=params['is_laz_upl']
    # obj.is_orp_upl=params['is_orp_upl']
    obj.is_problem=params['is_problem']
    obj.is_removed=params['is_removed']
    obj.remarks=params['remarks']
    obj.area_sqkm=params['area_sqkm']
    obj.save()
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
        params['area'] = feature.GetFieldAsInteger('area')
        params['block_name'] = feature.GetFieldAsString('block_name')
        params['processor'] = feature.GetFieldAsString('processor')
        params['sensor'] = feature.GetFieldAsString('sensor')
        params['base_used'] = feature.GetFieldAsString('base_used')
        params['flight_num'] = feature.GetFieldAsString('flight_num')
        params['mission_na'] = feature.GetFieldAsString('mission_na')
        params['date_flown'] = feature.GetFieldAsString('date_flown')
        params['x_shift'] = feature.GetFieldAsString('x_shift')
        params['y_shift'] = feature.GetFieldAsString('y_shift')
        params['z_shift'] = feature.GetFieldAsString('z_shift')
        params['height_dif'] = feature.GetFieldAsString('height_dif')
        params['rmse_val'] = feature.GetFieldAsString('rmse_val')
        params['cal_ref_pt'] = feature.GetFieldAsString('cal_ref_pt')
        params['val_ref_pt'] = feature.GetFieldAsString('val_ref_pt')
        params['floodplain'] = feature.GetFieldAsString('floodplain')
        params['pl1_suc'] = feature.GetFieldAsString('pl1_suc')
        params['pl2_suc'] = feature.GetFieldAsString('pl2_suc')
        params['is_adjuste'] = feature.GetFieldAsString('is_adjuste')
        # params['is_laz_adj'] = feature.GetFieldAsString('is_laz_adj')
        # params['is_orp_adj'] = feature.GetFieldAsString('is_orp_adj')
        # params['is_laz_upl'] = feature.GetFieldAsString('is_laz_upl')
        # params['is_orp_upl'] = feature.GetFieldAsString('is_orp_upl')
        params['is_problem'] = feature.GetFieldAsString('is_problem')
        params['is_removed'] = feature.GetFieldAsString('is_removed')
        params['remarks'] = feature.GetFieldAsString('remarks')
        params['area_sqkm'] = feature.GetFieldAsString('area_sqkm')

        # print params
        print 'Creating object...'
        try:
            obj = create_object(params)
            print '#' * 40
            print i, '/', feature_count
            print 'UID:', obj.uid
            print 'block_name:', obj.block_name
            print 'sensor:', obj.sensor
            print 'processor:', obj.processor
            print 'flight_num:', obj.flight_num
            print 'mission_na:', obj.mission_na
            print 'date_flown:', obj.date_flown
        except Exception:
            print 'Error creating or getting object!'
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
