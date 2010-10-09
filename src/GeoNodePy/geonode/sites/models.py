from django.conf import settings
from django.db import models
from geonode.maps.models import Layer, Map
from django.contrib.auth.models import User, Permission
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError

# Create your models here.
class UserSite(models.Model):
    owner = models.ForeignKey(User, blank=False, null=False)
    title = models.CharField(_('Site Title'), max_length=255, blank=False, null=False)
    urlSuffix = models.CharField(_('Site URL'), max_length=255, blank=False, null=False)
    map = models.ForeignKey(Map, blank=True, null=True)
    content = models.TextField(_('Site Content'), blank=True, null=True)
    banner_image = models.ImageField(upload_to='sitemedia/' + str(urlSuffix) +'/img')
    css_file = models.FileField(upload_to='sitemedia/' + str(urlSuffix) + '/img')

    def __unicode__(self):
        return u"Title: %s , URL: http://worldmap.harvard.edu/%s" % (self.title, self.urlSuffix)    
    
    
class UserSiteLayer(models.Model):
    usersite = models.ForeignKey(UserSite, blank=False, null=False)
    layer = models.ForeignKey(Layer, blank=False, null=False)
    
    def __unicode__(self):
        return u"URL: %s , Layer: %s" % (self.title, self.layer)   