from geonode.settings import GEONODE_APPS
import geonode.settings as settings
import codecs
from geonode.datarequests.models import LipadOrgType
import re
import os
import traceback

csv_path = os.getcwd()+'/scripts/utils/datarequests/org_type.csv'
if not os.path.isfile(csv_path):
    print '{0} file not found! Exiting.'.format(csv_path)
    exit(1)
print csv_path
# with codecs.open(csv_path, 'r', 'utf-8') as open_file:
with open(csv_path, 'r') as open_file:
    skip_once = False #to skip once (first column)
    request_list = []
    counter = 0
    for line in open_file:
        counter += 1
        if skip_once:
            skip_once = False
            continue
        tokens = line.strip().split(',')
        org_type = tokens[0].strip()
        org_type_main = tokens[1].strip()
        try:
            model_object = LipadOrgType.objects.get(val=str(org_type),
                                                display_val=str(org_type_main))
            print ('it already exists')
        except:
            try:
                model_object = LipadOrgType(val=str(org_type),
                                                display_val=str(org_type_main))
                model_object.save()
                print str(counter) + '. Saved: ', model_object.val

            except Exception as e:
                print e
                print traceback.print_exc()
                exit(1)
