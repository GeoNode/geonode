import geonode.settings as settings
from geonode.geoserver.helpers import ogc_server_settings
from osgeo import ogr
from shapely.wkb import loads
from shapely.geometry import Polygon
from geonode.cephgeo.models import CephDataObject, UserJurisdiction
import math
from shapely.ops import cascaded_union

def get_juris_tiles(juris_shp):
    total_data_size = 0
    min_x =  int(math.floor(juris_shp.bounds[0] / float(settings._TILE_SIZE)) * settings._TILE_SIZE)
    max_x =  int(math.ceil(juris_shp.bounds[2] / float(settings._TILE_SIZE)) * settings._TILE_SIZE)
    min_y =  int(math.floor(juris_shp.bounds[1] / float(settings._TILE_SIZE)) * settings._TILE_SIZE)
    max_y =  int(math.ceil(juris_shp.bounds[3] / float(settings._TILE_SIZE)) * settings._TILE_SIZE)
    tile_list = []
    for tile_y in xrange(min_y+settings._TILE_SIZE, max_y+settings._TILE_SIZE, settings._TILE_SIZE):
        for tile_x in xrange(min_x, max_x, settings._TILE_SIZE):
            tile_ulp = (tile_x, tile_y)
            tile_dlp = (tile_x, tile_y - settings._TILE_SIZE)
            tile_drp = (tile_x + settings._TILE_SIZE, tile_y - settings._TILE_SIZE)
            tile_urp = (tile_x + settings._TILE_SIZE, tile_y)
            tile = Polygon([tile_ulp, tile_dlp, tile_drp, tile_urp])
            
            if not tile.intersection(juris_shp).is_empty:
                tile_list.append(tile)
                
    return tile_list

def get_juris_data_size(juris_shp):
    tile_list = get_juris_tiles(juris_shp)
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
    
def assign_grid_refs(user):
    shapefile = UserJurisdiction.objects.get(user=user).jurisdiction_shapefile
    gridref_list = []
    
    for tile in get_juris_tiles(shapefile):
        (minx, miny, maxx, maxy) = tile.bounds
        gridref = '"E{0}N{1}"'.format(minx / settings._TILE_SIZE, maxy / settings._TILE_SIZE,)
        gridref_list .append(gridref)
    
    gridref_jquery = json.dumps(gridref_list)
    
    try:
        tile_list_obj = UserTiles.objects.get(user=user)
        tile_list_obj.gridref_list = gridref_jquery
    except ObjectDoesNotExist as e:
        tile_list_obj = UserTiles(user=user, gridref_list=gridref_jquery)
    finally:
        tile_list_obj.save()

def get_shp_ogr(juris_shp_name):
    source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(settings.DATABASE_HOST,settings.GIS_DATABASE_NAME,settings.DATABASE_USER,settings.DATABASE_PASSWORD)))
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
