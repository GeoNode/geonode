from actstream.models import Action
from geonode.eula.models import AnonDownloader
from geonode.reports.models import DownloadCount
from datetime import datetime, timedelta

datetoappend = datetime.strptime((datetime.now()-timedelta(days=3)).strftime('%U-%Y')+'-3','%U-%Y-%w') #timedelta to start week count days from sunday; days=3 meaning week count if from wednesday to tuesday
layer_count = {}
auth_list = Action.objects.filter(verb='downloaded').order_by('timestamp')
for auth in auth_list:
    if auth.timestamp.strftime('%U-%Y') not in layer_count:
           layer_count[auth.timestamp.strftime('%U-%Y')] = {
            "cov": 0,
            "doc": 0,
            "fhm": 0,
            "dtm": 0,
            "dsm": 0,
            "laz": 0,
            "ortho": 0,
            "sar": 0,
            "others": 0,
        }
    if auth.action_object.csw_type == 'document':
        layer_count[auth.timestamp.strftime('%U-%Y')]['doc'] += 1
    else:
        if 'coverage' in auth.action_object.typename:
            layer_count[auth.timestamp.strftime('%U-%Y')]['cov'] += 1
        elif 'fh' in auth.action_object.typename:
            layer_count[auth.timestamp.strftime('%U-%Y')]['fhm'] += 1
        elif 'dtm' in auth.action_object.typename:
            layer_count[auth.timestamp.strftime('%U-%Y')]['dtm'] += 1
        elif 'dsm' in auth.action_object.typename:
            layer_count[auth.timestamp.strftime('%U-%Y')]['dsm'] += 1
        elif 'laz' in auth.action_object.typename:
            layer_count[auth.timestamp.strftime('%U-%Y')]['laz'] += 1
        elif 'ortho' in auth.action_object.typename:
            layer_count[auth.timestamp.strftime('%U-%Y')]['ortho'] += 1
        elif 'sar' in auth.action_object.typename:
            layer_count[auth.timestamp.strftime('%U-%Y')]['sar'] += 1
        else:
            layer_count[auth.timestamp.strftime('%U-%Y')]['others'] += 1

anon_list = AnonDownloader.objects.all().order_by('date')
for anon in anon_list:
    if anon.date.strftime('%U-%Y') not in layer_count:
        layer_count[anon.date.strftime('%U-%Y')] = {
            "cov": 0,
            "doc": 0,
            "fhm": 0,
            "dtm": 0,
            "dsm": 0,
            "laz": 0,
            "ortho": 0,
            "sar": 0,
            "others": 0,
        }
    if anon.anon_document:
        layer_count[anon.date.strftime('%U-%Y')]['doc'] += 1
    else:
        if 'coverage' in anon.anon_layer.typename:
            layer_count[anon.date.strftime('%U-%Y')]['cov'] += 1
        elif 'fh' in anon.anon_layer.typename:
            layer_count[anon.date.strftime('%U-%Y')]['fhm'] += 1
        elif 'dtm' in anon.anon_layer.typename:
            layer_count[anon.date.strftime('%U-%Y')]['dtm'] += 1
        elif 'dsm' in anon.anon_layer.typename:
            layer_count[anon.date.strftime('%U-%Y')]['dsm'] += 1
        elif 'laz' in anon.anon_layer.typename:
            layer_count[anon.date.strftime('%U-%Y')]['laz'] += 1
        elif 'ortho' in anon.anon_layer.typename:
            layer_count[anon.date.strftime('%U-%Y')]['ortho'] += 1
        elif 'sar' in anon.anon_layer.typename:
            layer_count[anon.date.strftime('%U-%Y')]['sar'] += 1
        else:
            layer_count[anon.date.strftime('%U-%Y')]['others'] += 1
pprint(layer_count)

context_dict = {
    "layer_count": layer_count,
}
# list = download objects . all
# for obj in list
#     obj.create = 9
#     ob.save()
