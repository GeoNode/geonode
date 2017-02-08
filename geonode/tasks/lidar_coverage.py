import geonode.settings as settings

from django.contrib.auth.models import Group
from geonode.layers.models import Layer
from guardian.shortcuts import assign_perm
from layer_style import style_update
from osgeo import ogr
from thumbnail_permission import update_thumb_perms
import os
import psycopg2
import subprocess

# Requirement: lidar_coverage layer must already exist in
# geonode,geoserver,postgis

# connect to db
source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format
                   (settings.DATABASE_HOST, settings.GIS_DATABASE_NAME,
                    settings.DATABASE_USER, settings.DATABASE_PASSWORD)))
conn = psycopg2.connect(("host={0} dbname={1} user={2} password={3}".format
                         (settings.DATABASE_HOST, settings.GIS_DATABASE_NAME,
                          settings.DATABASE_USER, settings.DATABASE_PASSWORD)))
cur = conn.cursor()


# Set permission to 2 SUC groups
def lidar_coverage_permission(layer):
    try:
        pl1_group = Group.objects.get(name='phil-lidar-1-sucs')
        pl2_group = Group.objects.get(name='phil-lidar-2-sucs')
        # assign view permission
        assign_perm('view_resourcebase', pl1_group, layer.get_self_resource())
        assign_perm('view_resourcebase', pl2_group, layer.get_self_resource())
        # assign download permission
        assign_perm('download_resourcebase', pl1_group,
                    layer.get_self_resource())
        assign_perm('download_resourcebase', pl2_group,
                    layer.get_self_resource())
    except:
        print 'Error setting permission of LIDAR COVERAGE'


def lidar_coverage_metadata():
    try:
        # Absolute mount path of lidar coverage must be the same for all lipad
        path = '''/mnt/pmsat-nas_geostorage/DAD/COVERAGES/lipad_lidar_coverage/lidar_coverage.shp'''
    except:
        print 'ERROR GETTING LIDAR COVERAGE PATH'
    try:
        # Replace lidar_coverage shapefile in postgis
        subprocess.check_output('shp2pgsql -D -d -I -s 32651 ' + path +
                                ' lidar_coverage_1 | psql -h ' + settings.DATABASE_HOST +
                                ' -U ' + settings.DATABASE_USER + ' -d ' + settings.DATASTORE_DB,
                                shell=True, env=dict(os.environ, PGPASSWORD=settings.DATABASE_PASSWORD))
    except:
        print 'ERROR EXECUTING SHP2PGSQL COMMAND'

    # Rename columns in lidar_coverage table
    fid_query = 'alter table lidar_coverage_1 rename column gid to fid'
    try:
        cur.execute(fid_query)
        conn.commit()
    except psycopg2.ProgrammingError:
        print 'FID QUERY ERROR'
        conn.rollback()
        # continue
    the_geom_query = 'ALTER TABLE lidar_coverage_1 RENAME COLUMN geom to the_geom'
    try:
        cur.execute(the_geom_query)
        conn.commit()
    except psycopg2.ProgrammingError:
        print 'GEOM QUERY ERROR'
        conn.rollback()

    # Update metadata
    layer = Layer.objects.get(name='lidar_coverage_1')
    layer.abstract = '''The layer contains the following metadata per block:
                - Sensor used
                - Processor (DREAM or Phil-LiDAR 1)
                - Flight_Number
                - Mission_Name
                - Date_Flown
                - Shifting values: X_Shift_m, Y_Shift_m, Z_Shift_m
                - Height_difference_m
                - RMSE_Val_m
                - Cal_Ref_Pt: list of calibration reference points per block
                - Val_Ref_Pt: list of validation reference points per block
                    '''
    layer.title = 'LiDAR Coverage'

    style_update(layer, 'Boundary')
    update_thumb_perms(layer)
    lidar_coverage_permission(layer)

    layer.save()
    print 'FINISHED UPDATING LIDAR COVERAGE'
