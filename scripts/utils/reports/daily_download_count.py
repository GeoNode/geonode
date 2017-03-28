from geonode.settings import GEONODE_APPS
import geonode.settings as settings
from actstream.models import Action
from geonode.eula.models import AnonDownloader
from geonode.reports.models import DownloadCount, SUCLuzViMin, DownloadTracker
from datetime import datetime, timedelta
from geonode.layers.models import Layer
from geonode.cephgeo.models import FTPRequest, FTPRequestToObjectIndex, DataClassification
from geonode.people.models import Profile

from osgeo import ogr
from shapely.geometry import Polygon
from shapely.wkb import loads
from shapely.ops import cascaded_union

global layer_count, source
layer_count = {}
source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(settings.DATABASE_HOST,settings.DATASTORE_DB,settings.DATABASE_USER,settings.DATABASE_PASSWORD)))

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
            luzvimin = SUCLuzViMin.objects.filter(suc=SUC)[0].luzvimin
        except:
            luzvimin = "Luzvimin_others"
    else:
        luzvimin = "Luzvimin_others"
        try:
            layer_query = Layer.objects.get(typename=data['typename'])
        except:
            return luzvimin
        keyword_list = layer_query.keywords.names()
        for eachkeyword in keyword_list:
            try:
                luzvimin = SUCLuzViMin.objects.filter(suc=eachkeyword)[0].luzvimin
                break
            except Exception as e:
                print (layer_query.typename + ' - ' + str(e))
    return luzvimin

def add_to_count(category, typename):
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
        layer_count[category]['FHM'] += 1
    elif 'dtm' in typename:
        layer_count[category]['DTM'] += 1
    elif 'dsm' in typename:
        layer_count[category]['DSM'] += 1
    elif 'laz' in typename:
        layer_count[category]['LAZ'] += 1
    elif 'ortho' in typename:
        layer_count[category]['ORTHO'] += 1
    elif 'sar' in typename:
        layer_count[category]['SAR'] += 1
    elif 'coverage' in typename:
        layer_count[category]['Coverage'] += 1
    elif 'dem' in typename:
        layer_count[category]['Coverage'] += 1
    elif 'mkp' in typename:
        layer_count[category]['Coverage'] += 1
    elif any(lidar2keyword in typename for lidar2keyword in ['aquaculture', 'mangroves', 'agrilandcover', 'agricoastlandcover', 'irrigation', 'streams', 'wetlands', 'trees', 'ccm', 'chm', 'agb', 'power']):
        layer_count[category]['Resource'] += 1
    else:
        layer_count[category]['Others'] += 1
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
                            add_to_count(luzvimin, FTPtype)
                            add_to_count('monthly', FTPtype)
                    elif getattr(each_object,attr_type) == 'dataset' or not getattr(each_object,attr_type): #for DownloadTracker(if==dataset) or AnonDownloader(if not empty) therefore layer
                        luzvimin = get_luzvimin({
                            "typename": getattr(each_object,attr_filename),
                            "grid_ref": False
                            })
                        add_to_count(luzvimin, getattr(each_object,attr_filename))
                        add_to_count('monthly', getattr(each_object,attr_filename))
                    else: #else document
                        add_to_monthlyc('monthly')

def save_to_dc(minusdays,count_dict):
    datetoanalyze = datetime.strptime((datetime.now()-timedelta(days=minusdays)).strftime('%d-%m-%Y'),'%d-%m-%Y')
    for category, eachdict in count_dict.iteritems():
        if category == 'Luzon' or category == 'Visayas' or category == 'Mindanao' or category == 'Luzvimin_others':
            chart_group = 'luzvimin'
        elif category == 'monthly':
            chart_group = 'monthly'
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
