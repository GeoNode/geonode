from django.db import models
from geonode.layers.models import Layer
from geonode import settings
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
    SUCCESS = 0
    PENDING = 1
    ERROR = 2

class FTPRequest(models.Model):
    name        = models.CharField(max_length=30)
    datetime    = models.DateTimeField()
    user        = models.ForeignKey(User, null=False, blank=False)
    status      = enum.EnumField(FTPStatus, default=FTPStatus.PENDING)

class EULA(models.Model):
    user = models.ForeignKey(User, null=False, blank=False)
    document = models.FileField(upload_to=settings.MEDIA_ROOT)
    
class FTPRequestToObjectIndex(models.Model):
    # FTPRequest
    ftprequest = models.ForeignKey(FTPRequest, null=False, blank=False)
    # CephObject
    cephobject = models.ForeignKey(CephDataObject, null=False, blank=False)
    
