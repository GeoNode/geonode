import math
import sys
import traceback
from pprint import pprint
from celery.task import task
from osgeo import ogr

from shapely.wkb import loads
from shapely.geometry import Polygon
from shapely.ops import cascaded_union

from django.core.exceptions import ObjectDoesNotExist
from django.utils import simplejson as json

import geonode.settings as settings

from geonode.geoserver.helpers import ogc_server_settings
from geoserver.catalog import Catalog
from geonode.cephgeo.models import CephDataObject, UserJurisdiction, UserTiles
from geonode.datarequests.models import DataRequestProfile
from geonode.datarequests.utils import  get_place_name, get_area_coverage

from django.core.mail import send_mail

@task(name='geonode.tasks.jurisdiction2.compute_size_update', queue='jurisdiction')
def compute_size_update(requests_query_list, area_compute = True, data_size = True, save=True):
    pprint("Updating requests data size and area coverage")
    if len(requests_query_list) < 1:
        pprint("Requests for update is empty")
    else:
        for r in requests_query_list:
            pprint("Updating request id:{0}".format(r.pk))
            shapefile = get_shp_ogr(r.jurisdiction_shapefile.name)
            if shapefile:
                if area_compute:
                    r.area_coverage = get_area_coverage(shapefile)
                if data_size:
                    r.juris_data_size = get_juris_data_size(shapefile)
                
                if save:
                    r.save()

def get_juris_tiles(juris_shp, user):
    total_data_size = 0
    min_x =  int(math.floor(float(juris_shp.bounds[0]) / float(settings._TILE_SIZE))) * int(settings._TILE_SIZE)
    max_x =  int(math.ceil(float(juris_shp.bounds[2]) / float(settings._TILE_SIZE))) * int(settings._TILE_SIZE)
    min_y =  int(math.floor(float(juris_shp.bounds[1]) / float(settings._TILE_SIZE))) * int(settings._TILE_SIZE)
    max_y =  int(math.ceil(float(juris_shp.bounds[3]) / float(settings._TILE_SIZE))) * int(settings._TILE_SIZE)
    tile_list = []
    count = 0
    for tile_y in xrange(min_y+settings._TILE_SIZE, max_y+settings._TILE_SIZE, settings._TILE_SIZE):
        for tile_x in xrange(min_x, max_x, settings._TILE_SIZE):
            tile_ulp = (tile_x, tile_y)
            tile_dlp = (tile_x, tile_y - settings._TILE_SIZE)
            tile_drp = (tile_x + settings._TILE_SIZE, tile_y - settings._TILE_SIZE)
            tile_urp = (tile_x + settings._TILE_SIZE, tile_y)
            tile = Polygon([tile_ulp, tile_dlp, tile_drp, tile_urp])
            
            if not juris_shp.is_valid:
                juris_shp = juris_shp.convex_hull
                if juris_shp.convex_hull.is_valid:
                    juris_shp = juris_shp.convex_hull
                else:    
                    email_on_error(DataRequestProfile.objects.get(user=user).email,
                        "Your submitted shapefile is being considered invalid by the system because some of its borders maybe overlapping or intersecting each other. Please recheck your shapefile and submit a data request once more. Thank you.",
                        "A problem was encountered while processing your request"
                        )
                    return []
            
            if not tile.intersection(juris_shp).is_empty:
                tile_list.append(tile)
                count+=1
                if count > 1000:
                    return tile_list
                
    return tile_list

def get_juris_data_size(juris_shp, user):
    tile_list = get_juris_tiles(juris_shp, user)
    total_data_size = 0
    
    for tile in tile_list:
        (minx, miny, maxx, maxy) = tile.bounds
        gridref = "E{0}N{1}".format(minx / settings._TILE_SIZE, maxy / settings._TILE_SIZE,)
        georef_query = CephDataObject.objects.filter(name__startswith=gridref)
        total_size = 0
        for georef_query_objects in georef_query:
            total_size += georef_query_objects.size_in_bytes
        total_data_size += total_size
        
    return total_data_size

def assign_grid_ref_util(user):
    shapefile_name = UserJurisdiction.objects.get(user=user).jurisdiction_shapefile.name
    shapefile = get_shp_ogr(shapefile_name)
    gridref_list = []
    
    if shapefile:    
        pprint("Computing gridrefs for {0}".format(user.username))
        tiles = get_juris_tiles(shapefile, user)
        if len(tiles)>0:
            pprint("No tiles for {0}".format(user.username))
        else:
            for tile in tiles:
                (minx, miny, maxx, maxy) = tile.bounds
                gridref = '"E{0}N{1}"'.format(int(minx / settings._TILE_SIZE), int(maxy / settings._TILE_SIZE))
                gridref_list .append(gridref)
            
            gridref_jquery = json.dumps(gridref_list)
        
            try:
                tile_list_obj = UserTiles.objects.get(user=user)
                tile_list_obj.gridref_list = gridref_jquery
                tile_list_obj.save()
            except ObjectDoesNotExist as e:
                tile_list_obj = UserTiles(user=user, gridref_list=gridref_jquery)
                tile_list_obj.save() 
    else:
        pprint("Missing shapefile for {0}".format(user.username))

@task(name='geonode.tasks.jurisdiction2.assign_grid_refs', queue='jurisdiction')    
def assign_grid_refs(user):
    assign_grid_ref_util(user)

@task(name='geonode.tasks.jurisdiction2.assign_grid_refs_all',queue='jurisdiction')
def assign_grid_refs_all():
    user_jurisdictions = UserJurisdiction.objects.all()
    for uj in  user_jurisdictions:
        try:
            UserTiles.objects.get(user=uj.user)
        except ObjectDoesNotExist:
            assign_grid_ref_util(uj.user)

def get_shp_ogr(juris_shp_name):
    source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(settings.DATABASE_HOST,settings.DATASTORE_DB,settings.DATABASE_USER,settings.DATABASE_PASSWORD)))
    data = source.ExecuteSQL("select the_geom from "+str(juris_shp_name))
    shplist = []
    if data:
        for i in range(data.GetFeatureCount()):
            feature = data.GetNextFeature()
            shplist.append(loads(feature.GetGeometryRef().ExportToWkb()))
        juris_shp = cascaded_union(shplist)
        return juris_shp
    else:
        return None

def email_on_error(recipient, message, subject):
    send_mail(subject, message, settings.LIPAD_SUPPORT_MAIL, recipient, fail_silently= False)
    
