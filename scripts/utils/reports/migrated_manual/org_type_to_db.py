from geonode.settings import GEONODE_APPS
import geonode.settings as settings
from geonode.datarequests.models.data_request_profile import DataRequestProfile
import os
import traceback

csv_path = os.getcwd()+'/scripts/utils/reports/migrated_manual/org_type_to_db.csv'
if not os.path.isfile(csv_path):
    print '{0} file not found! Exiting.'.format(csv_path)
    exit(1)
print csv_path
with open(csv_path, 'r') as open_file:
    skip_once = True #to skip once (first row)
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
        org_type_sub = tokens[2].strip()
        try:
            model_object = DataRequestProfile.objects.get(id=str(request_id),email=str(email))
            model_object.org_type = org_type_sub
            model_object.save()
            print str(counter) + '. Saved: ', model_object.id, ' ',model_object.email
        except Exception as e:
            print e
            print traceback.print_exc()
            exit(1)
