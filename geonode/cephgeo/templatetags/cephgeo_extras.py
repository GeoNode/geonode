from django import template
from geonode.cephgeo.models import FTPStatus, DataClassification
register = template.Library()

def get_ftp_status_label(value): # Only one argument.
    """Converts a string into all lowercase"""
    try:
        return FTPStatus.labels[value]
    except:
        return "Invalid Status"

def get_data_class_label(value): # Only one argument.
    """Converts a string into all lowercase"""
    try:
        return DataClassification.labels[value]
    except:
        return "Invalid Status"
    
register.filter('get_ftp_status_label', get_ftp_status_label)
register.filter('get_data_class_label', get_data_class_label)
