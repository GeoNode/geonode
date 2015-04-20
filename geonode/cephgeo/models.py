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
    file_hash       = models.CharField(max_length=30)
    name            = models.CharField(max_length=100)
    last_modified   = models.DateTimeField()
    content_type    = models.CharField(max_length=20)
    geo_type        = models.CharField(max_length=20)
    grid_ref        = models.CharField(max_length=10)
    
    def __unicode__(self):
        return "{0}:{1}".format(self.name, self.geo_type)

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

class EULA(models.Model):
    user = models.ForeignKey(User, null=False, blank=False)
    document = models.FileField(upload_to=settings.MEDIA_ROOT)
    
class FTPRequestToObjectIndex(models.Model):
    # FTPRequest
    ftprequest = models.ForeignKey(FTPRequest, null=False, blank=False)
    # CephObject
    cephobject = models.ForeignKey(CephDataObject, null=False, blank=False)
    
