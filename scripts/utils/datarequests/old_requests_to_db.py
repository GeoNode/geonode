from geonode.settings import GEONODE_APPS
import geonode.settings as settings
import codecs
from geonode.datarequests.models import DataRequestProfile, LipadOrgType
import re
import os
import traceback

csv_path = os.getcwd()+'/scripts/utils/datarequests/old_requests.csv'
if not os.path.isfile(csv_path):
    print '{0} file not found! Exiting.'.format(csv_path)
    exit(1)
print csv_path
# with codecs.open(csv_path, 'r', 'utf-8') as open_file:
with open(csv_path, 'r') as open_file:
    skip_once = True #to skip once (first column)
    request_list = []
    counter = 0
    for line in open_file:
        counter += 1
        if skip_once:
            skip_once = False
            continue
        tokens = line.strip().split(',')
        request_id = tokens[0].strip()
        email = tokens[1].strip()
        org_type = tokens[2].strip()
        try:
            model_object = DataRequestProfile.objects.get(id=str(request_id),
                                                email=str(email))
            org_type_model = LipadOrgType.objects.get(val=org_type)
            model_object.org_type = org_type
            model_object.save()
            print str(model_object.request_id) + '- Saved: '
        except Exception as e:
            print e + str(request_id)
            print traceback.print_exc()
            exit(1)
