from geonode.settings import GEONODE_APPS
import geonode.settings as settings
import codecs
from geonode.reports.models import DownloadCount
import re
import os
import traceback
from datetime import datetime

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
            date = tokens[0].strip()
            category = tokens[1].strip()
            chart_group = tokens[2].strip()
            download_type = tokens[3].strip()
            count = tokens[4].strip()
            try:
                model_object = DownloadCount.objects.get(date=datetime.strptime(date,'%M-%Y').strftime('%Y-%M')+'-05',
                                                    category=str(category),
                                                    chart_group=str(chart_group),
                                                    download_type=str(download_type),
                                                    count=int(count))
                print ('it already exists')
            except:
                try:


                    model_object = DownloadCount(date=datetime.strptime(date,'%M-%Y').strftime('%Y-%M')+'-05',
                                                        category=str(category),
                                                        chart_group=str(chart_group),
                                                        download_type=str(download_type),
                                                        count=int(count))
                    print datetime.strptime(date,'%M-%Y').strftime('%Y-%M')+'-05'
                    print model_object.date
                    model_object.save()
                    print str(counter) + '. Saved: ', model_object.date, model_object.download_type

                except Exception as e:
                    print e
                    print traceback.print_exc()
                    exit(1)

csv_path = os.getcwd()+'/scripts/utils/reports/monthly_dl_count.csv'
# csv_path = raw_input('CSV complete file path:')
parse_reports_csv(csv_path)
