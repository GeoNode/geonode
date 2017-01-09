from geonode.settings import GEONODE_APPS
import geonode.settings as settings
import codecs
from geonode.reports.models import SUCLuzViMin
import re
import os
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")


def _is_in(aString, aList):
    for a in aList:
        if a in aString:
            return True
    return False


def parse_reports_csv(csv_path):
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
            province = tokens[1].strip()
            suc = tokens[2].strip()
            luzvimin = tokens[3].strip()
            try:
                model_object = SUCLuzViMin.objects.get(province=str(province),
                                                    suc=str(suc),
                                                    luzvimin=str(luzvimin))
                print ('it already exists')
            except:
                try:
                    model_object = SUCLuzViMin(province=str(province),
                                                        suc=str(suc),
                                                        luzvimin=str(luzvimin))
                    model_object.save()
                    print str(counter) + '. Saved: ', model_object.province, model_object.suc

                except Exception as e:
                    print e
                    print traceback.print_exc()
                    exit(1)

csv_path = os.getcwd()+'/scripts/utils/reports/SUC_LuzViMin.csv'
# csv_path = raw_input('CSV complete file path:')
parse_reports_csv(csv_path)
