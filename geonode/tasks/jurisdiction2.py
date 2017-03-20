import math
import sys
import traceback
import os
from pprint import pprint
from celery.task import task
from osgeo import ogr, osr
from pyproj import Proj, transform

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
        message = "The following area and data size computations have been completed:\n"
        for r in requests_query_list:
            pprint("Updating request id:{0}".format(r.pk))
            geometries = get_geometries_ogr(r.jurisdiction_shapefile.name)
            if area_compute:
                r.area_coverage = get_area_coverage(geometries)
            if data_size:
                r.juris_data_size = get_juris_data_size(dissolve_shp(geometries))
                
            if save:
                message += settings.SITEURL + str(r.get_absolute_url().replace('//','/')) + "\n"
                r.save()
        subject = "Area and data size computations done"
        recipient = [settings.LIPAD_SUPPORT_MAIL]
        send_mail(subject, message, settings.LIPAD_SUPPORT_MAIL, recipient, fail_silently= False)

def tile_floor(x):
    return int(math.floor(x / float(settings._TILE_SIZE)) * settings._TILE_SIZE)
    
def tile_ceiling(x):
    return int(math.ceil(x / float(settings._TILE_SIZE)) * settings._TILE_SIZE)

def get_juris_tiles(juris_shp, user=None):
    if not juris_shp.is_valid:
        juris_shp = juris_shp.convex_hull
        if not juris_shp.convex_hull.is_valid:
            if user:
                email_on_error(DataRequestProfile.objects.get(user=user).email,
                    "Your submitted shapefile is being considered invalid by the system because some of its borders maybe overlapping or intersecting each other. Please recheck your shapefile and submit a data request once more. Thank you.",
                    "A problem was encountered while processing your request"
                    )
            pprint("A problem with the shapefile was encountered")
            return []
    min_x =  tile_floor(juris_shp.bounds[0])
    #max_x =  int(math.ceil(float(juris_shp.bounds[2]) / float(settings._TILE_SIZE))) * int(settings._TILE_SIZE)
    max_x = tile_ceiling(juris_shp.bounds[2])
    #min_y =  int(math.floor(float(juris_shp.bounds[1]) / float(settings._TILE_SIZE))) * int(settings._TILE_SIZE)
    min_y = tile_floor(juris_shp.bounds[1])
    #max_y =  int(math.ceil(float(juris_shp.bounds[3]) / float(settings._TILE_SIZE))) * int(settings._TILE_SIZE)
    max_y = tile_ceiling(juris_shp.bounds[3])
    #if user:
    #    pprint("user: " + user.username + " bounds: "+str((min_x, min_y, max_x, max_y)))
    tile_list = []
    count = 0
    
    pprint("xrange y:"+str(list(xrange(min_y+settings._TILE_SIZE, max_y+settings._TILE_SIZE, settings._TILE_SIZE))))
    pprint("xrange x:"+str(list(xrange(min_x, max_x, settings._TILE_SIZE))))
    
    for tile_y in xrange(min_y+settings._TILE_SIZE, max_y+settings._TILE_SIZE, settings._TILE_SIZE):
        for tile_x in xrange(min_x, max_x, settings._TILE_SIZE):
            tile_ulp = (tile_x, tile_y)
            pprint("tile_ulp:"+str(tile_ulp))
            tile_dlp = (tile_x, tile_y - settings._TILE_SIZE)
            tile_drp = (tile_x + settings._TILE_SIZE, tile_y - settings._TILE_SIZE)
            tile_urp = (tile_x + settings._TILE_SIZE, tile_y)
            tile = Polygon([tile_ulp, tile_dlp, tile_drp, tile_urp])
            
            
            if not tile.intersection(juris_shp).is_empty:
                gridref = 'E{0}N{1}'.format(int(tile_x / settings._TILE_SIZE), int(tile_y / settings._TILE_SIZE))
                
                ceph_qs = CephDataObject.objects.filter(grid_ref = gridref)
                pprint("gridref:"+str(gridref)+" query_length:"+str(len(ceph_qs)))
                if ceph_qs.count() > 0:
                    tile_list.append(tile)
                #if len(tile_list) >= 1000:
                #    return tile_list
                
    return tile_list

def get_juris_data_size(geometry):
    tile_list = []
    pprint("Geom_type = "+geometry.geom_type)
    if geometry.geom_type == "Polygon":
        tile_list = get_juris_tiles(geometry)
    elif geometry.geom_type == "MultiPolygon":
        for g in geometry.geoms:
            tile_list.extend(get_juris_tiles(g))
    
    pprint("Number of tiles: "+str(len(tile_list)))
    
    total_data_size = 0
    
    for tile in tile_list:
        (minx, miny, maxx, maxy) = tile.bounds
        gridref = "E{0}N{1}".format(int(minx / settings._TILE_SIZE), int(maxy / settings._TILE_SIZE))
        georef_query = CephDataObject.objects.filter(name__startswith=gridref)
        total_size = 0
        for georef_query_objects in georef_query:
            total_size += georef_query_objects.size_in_bytes
        total_data_size += total_size
        
    return total_data_size

def assign_grid_ref_util(user):
    pprint("Computing gridrefs for {0}".format(user.username))
    shapefile_name = UserJurisdiction.objects.get(user=user).jurisdiction_shapefile.name
    geometry = dissolve_shp(get_geometries_ogr(shapefile_name))
    gridref_list = []
    
    if geometry:
        tiles = []
        if geometry.geom_type=='MultiPolygon':
            pprint("Tiling "+str(len(geometry)) + "geometries")
            for g in geometry.geoms:
                tiles.extend(get_juris_tiles(g, user))
        else:
            tiles = get_juris_tiles(geometry, user)
        
        pprint("Done with tiling")
        if len(tiles) < 1:
            pprint("No tiles for {0}".format(user.username))
        else:
            for tile in tiles:
                (minx, miny, maxx, maxy) = tile.bounds
                gridref = '"E{0}N{1}"'.format(int(minx / settings._TILE_SIZE), int(maxy / settings._TILE_SIZE))
                
                gridref_list.append(gridref)
                #if len(gridref_list) >= 1000:
                #    break
            
            if len(gridref_list)==1:
                pprint("gridref:"+gridref_list[0])
                pprint("Problematic shapefile for user {0} with shapefile {1}".format(user.username, shapefile_name ))
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

def get_geometries_ogr(juris_shp_name, dest_epsg=32651): #returns layer
    source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(settings.DATABASE_HOST,settings.DATASTORE_DB,settings.DATABASE_USER,settings.DATABASE_PASSWORD)))
    data = source.ExecuteSQL("select the_geom from "+str(juris_shp_name))

    if not data:
        return []
        
    #reprojection section
    src_epsg =  get_epsg(juris_shp_name)
    
    if src_epsg == 0:
        return []
    
    src_sref = osr.SpatialReference()
    src_sref.ImportFromEPSG(src_epsg)
    
    dest_sref = osr.SpatialReference()
    dest_sref.ImportFromEPSG(dest_epsg)
    c_transform = osr.CoordinateTransformation(src_sref, dest_sref)
    
    geometry_list = []
    
    for i in range(data.GetFeatureCount()):
        f = data.GetNextFeature()
        geom = f.GetGeometryRef()
        if not src_epsg == dest_epsg:
            geom.Transform(c_transform)
        geomWkb = loads(geom.ExportToWkb())
        if not geomWkb.is_valid:
            geomWkb = geomWkb.convex_hull
        
        geometry_list.append(geomWkb)
            
    source = None
    data = None
    
    return geometry_list
        
def dissolve_shp(geometries):
    #take geometry, returns geometry
    pprint("dissolving geometries ")
    #shplist = []
    #for g in geometries:
    #    shplist.append(loads(g.ExportToWkb()))
    dissolved_geoms = cascaded_union(geometries)
    pprint("succesfully dissolved")
    return dissolved_geoms
    
def get_epsg(shp_name):
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
        username=settings.OGC_SERVER['default']['USER'],
        password=settings.OGC_SERVER['default']['PASSWORD'])
    
    l = cat.get_layer(shp_name)
    if not l:
        return 0
    src_proj = l.resource.projection
    src_epsg =  int(src_proj.split(':')[1])
    
    return src_epsg

def reproject(geom, src_epsg, dest_epsg=32651):
    if src_epsg == 0:
        return None
        
    if src_epsg == dest_epsg:
        return geom
    
    src_sref = osr.SpatialReference()
    src_sref.ImportFromEPSG(src_epsg)
    
    dest_sref = osr.SpatialReference()
    dest_sref.ImportFromEPSG(dest_epsg=32651)
    
    c_transform = osr.CoordinateTransformation(src_sref, dest_sref)
    
    return geom.Transform(c_transform)

def email_on_error(recipient, message, subject):
    send_mail(subject, message, settings.LIPAD_SUPPORT_MAIL, recipient, fail_silently= False)
