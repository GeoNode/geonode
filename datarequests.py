import csv
import datetime

from geonode.settings import GEONODE_APPS
from geonode.datarequests.models import DataRequestProfile

import geonode.settings as settings
import os, sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")


def get_requests_with_letter(data_set):
    return data_set.exclude(request_letter = None)
    
def get_requests_before_date(data_set, month, day, year):
    date = datetime.date(year, month, day)
    return data_set.filter(key_created_date__lte=date)

def get_requests_by_status(data_set, request_status):
    return data_set.filter(request_status=request_status)
    
def write_to_csv(data_set):
    with open('dr.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['ReqNumber','Name', 'Email', 'Status'])
        for dr in result:
            writer.writerow([str(dr.pk), dr.first_name+" "+dr.last_name, dr.email, dr.request_status])
            
def main(argv):
    result = get_requests_before_date(get_requests_with_letter(DataRequestProfile.objects),7,18,2016)
    write_to_csv(result)
    
if __name__ == "__main__":
    main(sys.argv[1:])
