import csv
import datetime

from geonode.settings import GEONODE_APPS
from geonode.datarequests.models import DataRequestProfile
from geonode.utils import get_juris_data_size, get_area_coverage

import geonode.settings as settings
import os, sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")


def get_requests_with_letter(data_set):
    return data_set.exclude(request_letter = None)

def get_requests_with_roi(data_set):
    return data_set.exclude(jurisdiction_shapefile = None)
    
def get_requests_before_date(data_set, month, day, year):
    date = datetime.date(year, month, day)
    return data_set.filter(key_created_date__lte=date)

def get_requests_by_status(data_set, request_status):
    return data_set.filter(request_status=request_status)

def compute_area_size(data_set):
    for dr in data_set:
        if dr.jurisdiction_shapefile:
            dr.area_coverage = get_area_coverage(dr.jurisdiction_shapefile.name)
            dr.save()

def compute_estimated_data_size(data_set):
    for dr in data_set:
        if dr.jurisdiction_shapefile:
            dr.juris_data_size = get_juris_data_size(dr.jurisdiction_shapefile.name)
            dr.save()
    
def write_to_csv(file_name, result):
    with open(file_name, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['ReqNumber','Name', 'Email', 'Status', 'Estimated Data Size', 'Area in Sq. Km'])
        for dr in result:
            writer.writerow([str(dr.pk), dr.first_name+" "+dr.last_name, dr.email, dr.request_status])
            
def main(argv):
    result_roi = get_requests_before_date(get_requests_with_roi(DataRequestProfile.objects),7,18,2016)
    write_to_csv("requests_with_rois.csv", results_roi)
    results_letter = get_requests_before_date(get_requests_with_letter(DataRequestProfile.objects),7,18,2016)
    write_to_csv("requests_with_letters.csv", results_letter)
    
if __name__ == "__main__":
    main(sys.argv[1:])
