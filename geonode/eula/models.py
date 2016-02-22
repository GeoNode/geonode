from django.db import models
from geonode.layers.models import Layer
from datetime import datetime
try:
    from django.conf import settings
    User = settings.AUTH_USER_MODEL
except ImportError:
    from django.contrib.auth.models import User
    
# Create your models here.
class EULALayerDownload(models.Model):
    date_time   = models.DateTimeField(default=datetime.now)
    user        = models.ForeignKey(User, null=False, blank=False)
    layer       = models.ForeignKey(Layer, null=False, blank=False)
    
    def __unicode__(self):
        return "{0}:{1}".format(self.user.username, self.layer.title)