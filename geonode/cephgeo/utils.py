from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from operator import itemgetter, attrgetter
import re
from changuito.proxy import CartProxy
from geonode.cephgeo.models import CephDataObject, DataClassification, MissionGridRef, SucToLayer, FTPRequestToObjectIndex, RIDF
from geonode.datarequests.models import DataRequestProfile

from osgeo import ogr
import shapely
from shapely.wkb import loads
import math
import geonode.settings as settings
from collections import defaultdict
import json
from shapely.geometry import Polygon
import datetime
from unidecode import unidecode

_TILE_SIZE = 1000
### For additional functions/definitions which may be needed by views

### Sample Ceph object entry:{'hash': '524f26771b90ccea598448b8b7a263b7',
###                     'name': 'JE3409_ortho.tif', 'bytes': 17299767,
###                     'last_modified': '2015-02-24T07:23:11.000Z', 'content_type': 'image/tiff', 'type': 'Orthophoto'}

### A mapping of file types to their associated file extensions

#EXT_TO_TYPE_DICT = {
#   ".tif": "orthophoto/DEM",
#   ".csv": "csv",
#   ".dbf": "shapefile",
#   ".prj": "shapefile",
#   ".sbn": "shapefile",
#   ".sbx": "shapefile",
#   ".shx": "shapefile",
#   ".kml": "kml",
#   ".laz": "laz"

#TYPE_TO_IDENTIFIER_DICT = {
#   "DEM-DTM"       : ["_DTM"],
#   "DEM-DSM"       : ["_DSM"],
#   "Orthophoto"    : ["_ortho"],
#}
SORT_TYPES = [ "name", "type", "uploaddate", "default"]
FTP_SORT_TYPES = [ "date", "status", "default" ]

TYPE_TO_IDENTIFIER_DICT = {
    ".laz"          : "LAZ file",
    "_dem.tif"      : "DEM TIF",
#    "_dsm.tif"      : "DSM TIF",
    "_ortho.tif"    : "Orthophoto",
}


#### returns classification of the file based on file extension
#### if no matches, result is an empty string
### DEPRECTATED ###
def file_classifier(file_name):

    ext_classification = ''
    for x in TYPE_TO_IDENTIFIER_DICT:
        if len(file_name) > len(TYPE_TO_IDENTIFIER_DICT[x]):
            if file_name.lower().endswith(x):
                ext_classification = TYPE_TO_IDENTIFIER_DICT[x]

    return ext_classification

def sort_by(sort_key, object_list, descending=False):
    if descending:
        return sorted(object_list,  key=itemgetter(sort_key), reverse=True)
    else:
        return sorted(object_list,  key=itemgetter(sort_key))

#def file_feature_classifier(file_name):
#   pass

### DEPRECTATED ###
def is_valid_grid_ref_old(grid_ref_string):
    ptn = re.compile('^[a-zA-Z]{2}[0-9]{4}$')
    if ptn.match(grid_ref_string) is not None:
        return True
    else:
        return False

def is_valid_grid_ref_range(grid_ref_string):
    ptn = re.compile('^[a-zA-Z]{2}[0-9]{4}\-[a-zA-Z ]{2}[0-9]{4}$')
    if ptn.match(grid_ref_string) is not None:
        return True
    else:
        return False

def is_valid_grid_ref(grid_ref_string):
    # E648N803_DSM
    ptn = re.compile('^[a-zA-Z]{1}-[0-9]{3}[a-zA-Z]{1}[0-9]{3,4}$')
    if ptn.match(grid_ref_string) is not None:
        return True
    else:
        return False

def ceph_object_ids_by_data_class(ceph_obj_list):
    obj_name_dict = dict()
    for obj in ceph_obj_list:
        if DataClassification.labels[obj.data_class] in obj_name_dict:
            obj_name_dict[DataClassification.labels[obj.data_class].encode('utf8')].append(obj.name.encode('utf8'))
        else:
            obj_name_dict[DataClassification.labels[obj.data_class].encode('utf8')] = [obj.name.encode('utf8'),]

    return obj_name_dict

def get_cart_datasize(request):
    cart = CartProxy(request)
    total_size = 0
    for item in cart:
        obj = CephDataObject.objects.get(id=int(item.object_id))
        total_size += obj.size_in_bytes

    return total_size

def get_data_class_from_filename(filename):
        data_classification = DataClassification.labels[DataClassification.UNKNOWN]

        for x in DataClassification.filename_suffixes:
            filename_patterns=x.split(".")
            if filename_patterns[0] in filename.lower() and filename_patterns[1] in filename.lower():
                data_classification = DataClassification.filename_suffixes[x]

        return data_classification

def tile_floor(x):
    return int(math.floor(x / float(_TILE_SIZE)) * _TILE_SIZE)

def tile_ceiling(x):
    return int(math.ceil(x / float(_TILE_SIZE)) * _TILE_SIZE)

def get_bounds_1x1km(shape):
    min_x, min_y, max_x, max_y = shape.bounds
    min_x = tile_floor(min_x)
    min_y = tile_floor(min_y)
    max_x = tile_ceiling(max_x)
    max_y = tile_ceiling(max_y)
    return min_x, min_y, max_x, max_y

def filter_gridref():
    gridref_list = MissionGridRef.objects.all()
    gridref_dictionary = defaultdict(list)
    for gridref in gridref_list:
        gridref_dictionary[gridref.grid_ref].append(gridref.fieldID)
    gridref_dictionary = {k:v for k,v in gridref_dictionary.items() }
    with open('geonode/georef_output.json', 'w') as fp:
        json.dump(gridref_dictionary,fp)

def tile_shp(tile_extents,eval_shp_poly,feature):
    # gridref_list = []
    min_x, min_y, max_x, max_y = tile_extents


    for tile_y in xrange(min_y+_TILE_SIZE, max_y+_TILE_SIZE, _TILE_SIZE): #georeference
        for tile_x in xrange(min_x, max_x, _TILE_SIZE):

            # 4 points of this tile
            tile_ulp = (tile_x, tile_y)
            tile_dlp = (tile_x, tile_y - _TILE_SIZE)
            tile_drp = (tile_x + _TILE_SIZE, tile_y - _TILE_SIZE)
            tile_urp = (tile_x + _TILE_SIZE, tile_y)

            # Grid Ref of this tile
            gridref = "E{0}N{1}".format(tile_x / _TILE_SIZE, tile_y / _TILE_SIZE,)
            # print gridref

            tile = Polygon([tile_ulp, tile_dlp, tile_drp, tile_urp])
            # Evaluate intersections
            if not tile.intersection(eval_shp_poly).is_empty:
                if len(MissionGridRef.objects.filter(fieldID=feature.GetField("UID"),grid_ref=str(gridref))) == 0:
                    # print gridref
                    georef = MissionGridRef.objects.create(fieldID=feature.GetField("UID"),grid_ref=str(gridref))
                    georef.save()

def iterate_over_features():
    #source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(settings.HOST_ADDR,settings.GIS_DATABASE_NAME,settings.DATABASE_USER,settings.DATABASE_PASSWORD)))
    source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(settings.DATABASE_HOST,settings.DATASTORE_DB,settings.DATABASE_USER,settings.DATABASE_PASSWORD)))
    layer = source.GetLayer(settings.LIDAR_COVERAGE)
    i = 0
    feature_count = layer.GetFeatureCount()
    for feature in layer:
        i+=1
        d = datetime.datetime.now()
        print "[{0}/{1}/{2} - {3}:{4}:{5}] Feature #{6} of {7} - {8}".format(d.day, d.month, d.year, d.hour, d.minute, d.second,i, feature_count, feature.GetField("Block_Name"))
        feature = layer.GetNextFeature()
        # print feature.GetField("Block_Name")
        geom = loads(feature.GetGeometryRef().ExportToWkb())
        bounds = get_bounds_1x1km(geom)
        tile_shp(bounds,geom,feature)


def map_blocks_suc():
    if "lipad" not in settings.BASEURL:
        source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(settings.HOST_ADDR,settings.GIS_DATABASE_NAME,settings.DATABASE_USER,settings.DATABASE_PASSWORD)))
    else:
        source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(settings.DATABASE_HOST,settings.DATASTORE_DB,settings.DATABASE_USER,settings.DATABASE_PASSWORD)))
    floodplain = source.GetLayer("fp_panay")
    blocks = source.GetLayer("lidar_panay")
    blocks_with_suc = defaultdict(lambda: defaultdict(str))
    rb_geomrefs = []
    rb_list = []
    block_list = []
    for i,riverbasin in enumerate(floodplain): #get list of geomrefs of riverbasins
        rb_list.append(riverbasin)
        riverbasin_geom = riverbasin.GetGeometryRef()
        rb_geomrefs.append(riverbasin_geom)
    for i,riverbasin in enumerate(rb_list):
        if riverbasin is None:
            print "None"
        else:
            blocks.SetSpatialFilter(None)
            rb_geom = rb_geomrefs[i] #get geometry of riverbasin
            blocks.SetSpatialFilter(rb_geom) #intersect rb_geomref to the layer coverage
            suc = str(riverbasin.GetFieldAsString("SUC"))
            for block in blocks: #list blocks that intersected with the rb's geomref
                block_list.append(block.GetFieldAsString("Block_Name"))
            blocks_with_suc["%s" % suc] = block_list
    for key,value in blocks_with_suc.items():
        value = list(set(value))
        for v in value:
            obj = SucToLayer.objects.create(suc=riverbasin.GetFieldAsString("SUC"),block_name=str(v))
            obj.save()

def get_ftp_details(ftp_request):
    dr = None

    try:
        drs = DataRequestProfile.objects.filter(profile = ftp_request.user)
        if len(drs)>0:
            dr = drs[0]
    except ObjectDoesNotExist:
        dr = None

    ftp_details = {}
    user = ftp_request.user
    ftp_details['user'] = user

    if ftp_request.user.organization:
        ftp_details['organization'] = user.organization
        ftp_details["organization_type"] = user.org_type
    elif dr:
        ftp_details['organization'] = dr.organization
        ftp_details["organization_type"] = dr.org_type
    else:
        ftp_details['organization'] = None
        ftp_details["organization_type"] = None

    ftp_details['total_number_of_tiles'] = ftp_request.num_tiles
    ftp_details['total_size'] = ftp_request.size_in_bytes
    ftp_details['number_of_laz'] = get_tiles_by_type(ftp_request, 1) #LAZ
    ftp_details['size_of_laz'] = get_bytes_by_type(ftp_request, 1) #LAZ
    ftp_details['number_of_dtm'] = get_tiles_by_type(ftp_request, 3) #DTM
    ftp_details['size_of_dtm'] = get_bytes_by_type(ftp_request, 3) #DTM
    ftp_details['number_of_dsm'] = get_tiles_by_type(ftp_request, 4) #DSM
    ftp_details['size_of_dsm'] = get_bytes_by_type(ftp_request, 4) #DSM
    ftp_details['number_of_ortho'] = get_tiles_by_type(ftp_request, 5) #Ortho
    ftp_details['size_of_ortho'] = get_bytes_by_type(ftp_request, 5) #Ortho

    return ftp_details

def get_tiles_by_type(ftp_request, data_type):
    request_to_tiles =  FTPRequestToObjectIndex.objects.filter(ftprequest = ftp_request).filter(cephobject__data_class=data_type)

    num_tiles = len(request_to_tiles)

    return num_tiles

def get_bytes_by_type(ftp_request, data_type):
    request_to_tiles =  FTPRequestToObjectIndex.objects.filter(ftprequest = ftp_request).filter(cephobject__data_class=data_type)
    size_in_bytes = 0

    for r in request_to_tiles:
        size_in_bytes += r.cephobject.size_in_bytes

    return size_in_bytes

#for testing of map_blocks_suc() uncomment this block:
# from collections import defaultdict
# from osgeo import ogr
# import shapely
# from shapely.wkb import loads
# import math
# import geonode.settings as settings
# from geonode.cephgeo.models import CephDataObject, DataClassification, MissionGridRef, SucToLayer
# if "lipad" not in settings.BASEURL:
#     source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(settings.HOST_ADDR,settings.GIS_DATABASE_NAME,settings.DATABASE_USER,settings.DATABASE_PASSWORD)))
# else:
#     source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(settings.DATABASE_HOST,settings.DATASTORE_DB,settings.DATABASE_USER,settings.DATABASE_PASSWORD)))
# floodplain = source.GetLayer("fp_panay")
# blocks = source.GetLayer("lidar_panay")
# blocks_with_suc = defaultdict(lambda: defaultdict(str))
# rb_geomrefs = []
# rb_list = []
# block_list = []
# for i,riverbasin in enumerate(floodplain): #get list of geomrefs of riverbasins
#     rb_list.append(riverbasin)
#     riverbasin_geom = riverbasin.GetGeometryRef()
#     rb_geomrefs.append(riverbasin_geom)
# for i,riverbasin in enumerate(rb_list):
#     if riverbasin is None:
#         print "None"
#     else:
#         blocks.SetSpatialFilter(None)
#         rb_geom = rb_geomrefs[i] #get geometry of riverbasin
#         blocks.SetSpatialFilter(rb_geom) #intersect rb_geomref to the layer coverage
#         suc = str(riverbasin.GetFieldAsString("SUC"))
#         for block in blocks: #list blocks that intersected with the rb's geomref
#             block_list.append(block.GetFieldAsString("Block_Name"))
#         blocks_with_suc["%s" % suc] = block_list
# for key,value in blocks_with_suc.items():
#     value = list(set(value))
#     for v in value:
#         obj = SucToLayer.objects.create(suc=riverbasin.GetFieldAsString("SUC"),block_name=str(v))
#         obj.save()
