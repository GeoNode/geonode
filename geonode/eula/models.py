from django.db import models
from geonode.layers.models import Layer
from geonode.documents.models import Document
from datetime import datetime
from django.utils.translation import ugettext_lazy as _
from geonode.base.models import ResourceBase
from geonode.people.models import OrganizationType
from django_enumfield import enum
try:
    from django.conf import settings
    User = settings.AUTH_USER_MODEL
except ImportError:
    from django.contrib.auth.models import User
from geonode.datarequests.models import LipadOrgType

# Create your models here.
class EULALayerDownload(models.Model):
    date_time   = models.DateTimeField(default=datetime.now)
    user        = models.ForeignKey(User, null=False, blank=False)
    layer       = models.ForeignKey(Layer, null=False, blank=False)

    def __unicode__(self):
        return "{0}:{1}".format(self.user.username, self.layer.title)

class AnonDownloader(models.Model):
    ORG_TYPE_CHOICES = LipadOrgType.objects.values_list('val', 'display_val')
    date = models.DateTimeField(auto_now=True)
    anon_first_name = models.CharField(_('First Name'), max_length=100)
    anon_last_name = models.CharField(_('Last Name'), max_length=100)
    anon_email = models.EmailField(_('Email'), max_length=50)
    anon_organization = models.CharField(_('Organization'), max_length=100)
    anon_purpose = models.CharField(_('Purpose'), max_length=100)
    anon_layer = models.CharField(_('Layer Name'), max_length=100, null=True, blank=True,)
    anon_orgtype = models.CharField(
        _('Organization Type'),
        max_length=100,
        choices=ORG_TYPE_CHOICES,
        default="Other",
        help_text='Organization type based on Phil-LiDAR1 Data Distribution Policy'
    )
    anon_orgother = models.CharField(
        _('If Other, please specify'),
        max_length=255,
        blank=True,
        null=True,
    )
    # anon_resourcebase = models.ForeignKey(ResourceBase, null=True, blank=True, related_name='anon_resourcebase')
    anon_document = models.CharField(_('Document Name'), max_length=100, null=True, blank=True,)
