from geonode.settings import GEONODE_APPS
import geonode.settings as settings
from actstream.models import Action
from geonode.eula.models import AnonDownloader
from geonode.reports.models import DownloadCount, SUCLuzViMin, DownloadTracker
from datetime import datetime, timedelta
from geonode.layers.models import Layer
from geonode.cephgeo.models import FTPRequest, FTPRequestToObjectIndex, DataClassification
from geonode.people.models import Profile

layer_count = {}

def get_luzvimin(iterate):
    layer_query = Layer.objects.get(typename=iterate['typename'])
    keyword_list = layer_query.keywords.values_list()
    try:
        for eachkeyword in keyword_list[0]:
            luzvimin_query = SUCLuzViMin.objects.filter(suc=eachkeyword)[0]
            luzvimin = luzvimin_query.luzvimin
            break
    except Exception as e:
        print (str(iterate['typename']) + ' - ' + str(e))
        luzvimin = "Luzvimin_others"
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

datetoappend = datetime.strptime((datetime.now()-timedelta(days=1)).strftime('%d-%m-%Y'),'%d-%m-%Y') #timedelta to start week count days from sunday; days=3 meaning week count if from wednesday to tuesday
# auth_list = Action.objects.filter(verb='downloaded').order_by('timestamp')
auth_list = DownloadTracker.objects.order_by('timestamp')
for auth in auth_list:
    if datetoappend == datetime.strptime(auth.timestamp.strftime('%d-%m-%Y'),'%d-%m-%Y'):#if datenow is timestamp
        getprofile_downloadtracker = Profile.objects.get(username=auth.actor)
        if not getprofile_downloadtracker.is_staff and not any('test' in var for var in [str(auth.actor), getprofile_downloadtracker.first_name, getprofile_downloadtracker.last_name]):
            if not auth.resource_type == 'document':
                luzvimin = get_luzvimin({
                    "timestamp": auth.timestamp,
                    "typename": auth.title,
                    })
                add_to_count(luzvimin, auth.title)
                add_to_count('monthly', auth.title)
            elif auth.resource_type == 'document':#if datenow is timestamp
                add_to_monthlyc('monthly')

anon_list = AnonDownloader.objects.all().order_by('date')
for anon in anon_list:
    if datetoappend == datetime.strptime(anon.date.strftime('%d-%m-%Y'),'%d-%m-%Y'):
        if not anon.anon_document:#if datenow is timestamp
            luzvimin = get_luzvimin({
                "timestamp": anon.date,
                "typename": anon.anon_layer.typename,
                })
            add_to_count(luzvimin, anon.anon_layer.typename)
            add_to_count('monthly', anon.anon_layer.typename)
        elif anon.anon_document:#if datenow is timestamp
            add_to_monthlyc('monthly')
ftp_list = FTPRequest.objects.all().order_by('date_time')
for ftp in ftp_list:
    if datetoappend == datetime.strptime(ftp.date_time.strftime('%d-%m-%Y'),'%d-%m-%Y'):
        getprofile_ftp = Profile.objects.get(username=ftp.user)
        if not getprofile_ftp.is_staff and not any('test' in var for var in [str(ftp.user), getprofile_ftp.first_name, getprofile_ftp.last_name]):
            type_list = FTPRequestToObjectIndex.objects.filter(ftprequest=ftp.id)
            for eachtype in type_list:
                add_to_count('monthly', DataClassification.gs_feature_labels[eachtype.cephobject._enum_data_class].lower())
print(layer_count)


for eachkey, eachdict in layer_count.iteritems():
    category = eachkey
    if category == 'Luzon' or category == 'Visayas' or category == 'Mindanao' or category == 'Luzvimin_others':
        chart_group = 'luzvimin'
    elif category == 'monthly':
        chart_group = 'monthly'
    for eachtype, eachvalue in eachdict.iteritems():
        if eachvalue:
            model_object = DownloadCount(date=str(datetoappend),
                                        category=str(category),
                                        chart_group=str(chart_group),
                                        download_type=str(eachtype),
                                        count=str(eachvalue))
            model_object.save()
            print str(datetoappend) +'-'+ str(category) +'-'+ str(chart_group) +'-'+ str(eachtype) +'-'+ str(eachvalue)
