from geonode.settings import GEONODE_APPS
import geonode.settings as settings
from actstream.models import Action
from geonode.eula.models import AnonDownloader
from geonode.reports.models import DownloadCount, SUCLuzViMin, DownloadTracker
from datetime import datetime, timedelta
from geonode.layers.models import Layer
from geonode.cephgeo.models import FTPRequest, FTPRequestToObjectIndex, DataClassification
from geonode.people.models import Profile

from osgeo import ogr, gdal
from shapely.geometry import Polygon
from shapely.wkb import loads
from shapely.ops import cascaded_union
import ast

gdal.UseExceptions()
global layer_count, source
layer_count = {}
source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(settings.DATABASE_HOST,settings.DATASTORE_DB,settings.DATABASE_USER,settings.DATABASE_PASSWORD)))

def get_area(typename):
    if typename[:4] == 'osm:' or typename == 'geonode:gerona_ccm':
        return 0
    shp_name = Layer.objects.get(typename=typename).name
    data = source.ExecuteSQL("select the_geom from "+str(shp_name))
    if not data: data = source.ExecuteSQL("select the_geom from "+str(shp_name)+"_extents")
    if not data: data = source.ExecuteSQL("select the_geom from "+str(shp_name)+"_1")
    shp_list = []
    for i in range(data.GetFeatureCount()):
        feature = data.GetNextFeature()
        shp_list.append(loads(feature.GetGeometryRef().ExportToWkb()))
    try:
        juris_shp = cascaded_union(shp_list)
        return juris_shp.area/1000000
    except:
        area = 0
        for eachshp in shp_list:
            area += eachshp.area
        return area/1000000

def get_SUC_using_gridref(abscissa, ordinate, _TILE_SIZE = 1000):
    data = source.ExecuteSQL("select * from "+settings.PL1_SUC_MUNIS)
    tile_ulp = "%s %s" % (abscissa, ordinate)
    tile_dlp = "%s %s" % (abscissa, ordinate - _TILE_SIZE)
    tile_drp = "%s %s" % (abscissa + _TILE_SIZE, ordinate - _TILE_SIZE)
    tile_urp = "%s %s" % (abscissa + _TILE_SIZE, ordinate)
    tilestr = "POLYGON ((%s, %s, %s, %s, %s))"% (tile_ulp, tile_dlp, tile_drp, tile_urp, tile_ulp)
    data.SetSpatialFilter(ogr.CreateGeometryFromWkt(tilestr))
    for feature in data:
        return feature.GetField("SUC")

def get_luzvimin(data):
    if data['grid_ref']:#If FTP
        east = int(data['grid_ref'].split('N')[0][1:])*1000
        north = int(data['grid_ref'].split('N')[1])*1000
        SUC = get_SUC_using_gridref(east,north)
        try:
            query = SUCLuzViMin.objects.filter(suc=SUC)[0].luzvimin
            luzvimin = SUC
        except:
            luzvimin = "Luzvimin_others"
    else:
        luzvimin = "Luzvimin_others"
        if data['keywords']:
            keyword_list = ast.literal_eval(data['keywords'])
        else:
            try:
                layer_query = Layer.objects.get(typename=data['typename'])
            except:
                print data['typename']
                return luzvimin
            keyword_list = layer_query.keywords.names()
        for eachkeyword in keyword_list:
            try:
                query = SUCLuzViMin.objects.filter(suc__iexact=eachkeyword)[0].luzvimin
                luzvimin = SUCLuzViMin.objects.filter(suc__iexact=eachkeyword)[0].suc
                break
            except Exception as e:
                pass
        if luzvimin == "Luzvimin_others": print data['typename']
    return luzvimin

def add_to_count(category, typename, count):
    if category not in layer_count:
        layer_count[category] = {
            "Coverage": 0,
            "Document": 0,
            "FHM": 0,
            "DTM": 0,
            "DSM": 0,
            "LAZ": 0,
            "ORTHO": 0,
            "SAR": 0,
            "Others": 0,
            "Resource":0,
        }
    if 'fh' in typename:
        layer_count[category]['FHM'] += count
    elif 'dtm' in typename:
        layer_count[category]['DTM'] += count
    elif 'dsm' in typename:
        layer_count[category]['DSM'] += count
    elif 'laz' in typename:
        layer_count[category]['LAZ'] += count
    elif 'ortho' in typename:
        layer_count[category]['ORTHO'] += count
    elif 'sar' in typename:
        layer_count[category]['SAR'] += count
    elif 'coverage' in typename:
        layer_count[category]['Coverage'] += count
    elif 'dem' in typename:
        layer_count[category]['Coverage'] += count
    elif 'mkp' in typename:
        layer_count[category]['Coverage'] += count
    elif any(lidar2keyword in typename for lidar2keyword in ['aquaculture', 'mangroves', 'agrilandcover', 'agricoastlandcover', 'irrigation', 'streams', 'wetlands', 'trees', 'ccm', 'chm', 'agb', 'power']):
        layer_count[category]['Resource'] += count
    else:
        layer_count[category]['Others'] += count
def add_to_monthlyc(category):
    if category not in layer_count:
        layer_count[category] = {
            "Coverage": 0,
            "Document": 0,
            "FHM": 0,
            "DTM": 0,
            "DSM": 0,
            "LAZ": 0,
            "ORTHO": 0,
            "SAR": 0,
            "Others": 0,
            "Resource": 0,
        }
    layer_count[category]['Document'] += 1

def main(minusdays, query_objects, attr_date, attr_actor, attr_type, attr_filename, FTP):
    datetoanalyze = datetime.strptime((datetime.now()-timedelta(days=minusdays)).strftime('%d-%m-%Y'),'%d-%m-%Y') #if minusdays = 1, analyzes downloads day before; because python code is ran early morning
    for each_object in query_objects.order_by(attr_date):
        if datetoanalyze == datetime.strptime(getattr(each_object, attr_date).strftime('%d-%m-%Y'),'%d-%m-%Y'):
            if attr_actor:
                getprofile = Profile.objects.get(username=getattr(each_object,attr_actor))
                if not getprofile.is_staff and not any('test' in var for var in [str(getattr(each_object,attr_actor)),getprofile.first_name,getprofile.last_name]):
                    if FTP:
                        type_list = FTPRequestToObjectIndex.objects.filter(ftprequest=each_object.id)
                        for eachtype in type_list:
                            FTPtype = DataClassification.gs_feature_labels[eachtype.cephobject._enum_data_class].lower()
                            luzvimin = get_luzvimin({
                                "grid_ref": eachtype.cephobject.grid_ref,
                                })
                            add_to_count(luzvimin, FTPtype, 1)
                            add_to_count('monthly', FTPtype, 1)
                            add_to_count('area', FTPtype, 1)
                    elif getattr(each_object,attr_type) == 'dataset' or not getattr(each_object,attr_type): #for DownloadTracker(if==dataset) or AnonDownloader(if not empty) therefore layer
                        keywordslist = getattr(each_object,'keywords') if attr_filename == 'title' else False #for DownloadTracker only
                        luzvimin = get_luzvimin({
                            "typename": getattr(each_object,attr_filename),
                            "grid_ref": False,
                            "keywords": keywordslist
                            })
                        area = int(get_area(getattr(each_object,attr_filename)))
                        add_to_count(luzvimin, getattr(each_object,attr_filename),1)
                        add_to_count('monthly', getattr(each_object,attr_filename),1)
                        add_to_count('area', getattr(each_object,attr_filename), area)
                    else: #else document
                        add_to_monthlyc('monthly')

def save_to_dc(minusdays,count_dict):
    datetoanalyze = datetime.strptime((datetime.now()-timedelta(days=minusdays)).strftime('%d-%m-%Y'),'%d-%m-%Y')
    for category, eachdict in count_dict.iteritems():
        if category == 'monthly':
            chart_group = 'monthly'
        elif category == 'area':
            chart_group = 'area'
            category = 'monthly'
        else:
            chart_group = 'luzvimin'
        for eachtype, eachvalue in eachdict.iteritems():
            if eachvalue:
                model_object = DownloadCount(date=str(datetoanalyze),
                                            category=str(category),
                                            chart_group=str(chart_group),
                                            download_type=str(eachtype),
                                            count=str(eachvalue))
                model_object.save()
                print str(datetoanalyze) +'-'+ str(category) +'-'+ str(chart_group) +'-'+ str(eachtype) +'-'+ str(eachvalue)

if __name__ == "__main__":
    minusdays = 1
    layer_count = {}
    main(minusdays,DownloadTracker.objects, 'timestamp', 'actor','resource_type','title', False)
    main(minusdays,AnonDownloader.objects, 'date', False,'anon_document','anon_layer', False)
    main(minusdays,FTPRequest.objects,'date_time','user','','',True)
    print(layer_count)

    save_to_dc(minusdays,layer_count)
