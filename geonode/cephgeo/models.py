from django.db import models
from geonode.layers.models import Layer
from geonode import settings
from datetime import datetime
import json

try:
    from django.conf import settings
    User = settings.AUTH_USER_MODEL
except ImportError:
    from django.contrib.auth.models import User

from django_enumfield import enum


class CephDataObject(models.Model):
    size_in_bytes   = models.IntegerField()
    file_hash       = models.CharField(max_length=40)
    name            = models.CharField(max_length=100)
    last_modified   = models.DateTimeField()
    content_type    = models.CharField(max_length=20)
    geo_type        = models.CharField(max_length=20)
    grid_ref        = models.CharField(max_length=10)
    
    def __unicode__(self):
        return "{0}:{1}".format(self.name, self.geo_type)

class DataClassification(enum.Enum):
    UNKNOWN = 0
    LAZ = 1
    DEM = 2
    DTM = 3
    DSM = 4
    ORTHOPHOTO = 5
    
    labels = {
        UNKNOWN     : "Unknown Type",
        LAZ			: "LAZ",
        DEM 		: "DEM TIF",
        DSM     	: "DSM TIF",
        DTM 		: "DTM TIF",
        ORTHOPHOTO  : "Orthophoto",}
    
    filename_suffixes = {
        ".laz"			: LAZ,
        "_dem.tif" 		: DEM,
        "_dsm.tif" 		: DSM,
        "_dtm.tif" 		: DTM,
        "_ortho.tif"	: ORTHOPHOTO,}
    
    def get_label_from_filename(filename):
        data_classification = labels[UNKNOWN]
        
        for x in filename_suffixes:
            if len(file_name) > len(filename_suffixes[x]):
                if file_name.lower().endswith(x):
                    data_classification = filename_suffixes[x]
            
        return data_classification

class FTPStatus(enum.Enum):
    DONE = 0
    PENDING = 1
    ERROR = 2
    DUPLICATE = 3
    
    labels = {
        DONE: 'Done',
        PENDING: 'Pending',
        ERROR:   'Error',
        DUPLICATE: 'Duplicate',}

class FTPRequest(models.Model):
    name        = models.CharField(max_length=50)
    date_time   = models.DateTimeField(default=datetime.now)
    user        = models.ForeignKey(User, null=False, blank=False)
    status      = enum.EnumField(FTPStatus, default=FTPStatus.PENDING)
    size_in_bytes   = models.IntegerField()
    num_tiles   = models.IntegerField()
    
    def __unicode__(self):
        return "{0}:{1}".format(self.name, self.user.username)

class EULA(models.Model):
    user = models.ForeignKey(User, null=False, blank=False)
    document = models.FileField(upload_to=settings.MEDIA_ROOT)
    
class FTPRequestToObjectIndex(models.Model):
    # FTPRequest
    ftprequest = models.ForeignKey(FTPRequest, null=False, blank=False)
    # CephObject
    cephobject = models.ForeignKey(CephDataObject, null=False, blank=False)

    
