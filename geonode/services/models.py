import logging
from django.conf import settings
from django.db import models
from geoserver.catalog import FailedRequestError, Catalog
from taggit.managers import TaggableManager

from geonode.base.models import ResourceBase
from geonode.services.enumerations import SERVICE_TYPES, SERVICE_METHODS, GXP_PTYPES
from geonode.layers.models import Layer 
from geonode.people.models import Profile
from django.utils.translation import ugettext_lazy as _
from django.db.models import signals
from geonode.people.enumerations import ROLE_VALUES

STATUS_VALUES = [
    'pending',
    'failed',
    'process'
]

logger = logging.getLogger("geonode.services")

"""
geonode.services
"""
class Service(ResourceBase):
    """
    Service Class to represent remote Geo Web Services
    """

    type = models.CharField(max_length=4, choices=SERVICE_TYPES)
    method = models.CharField(max_length=1, choices=SERVICE_METHODS)
    base_url = models.URLField(unique=True,db_index=True) # with service, version and request etc stripped off
    version = models.CharField(max_length=10, null=True, blank=True)
    name = models.CharField(max_length=255, unique=True,db_index=True) #Should force to slug?
    description = models.CharField(max_length=255, null=True, blank=True)
    online_resource = models.URLField(False, null=True, blank=True)
    fees = models.CharField(max_length=1000, null=True, blank=True)
    access_contraints = models.CharField(max_length=255, null=True, blank=True)
    connection_params = models.TextField(null=True, blank=True)
    username = models.CharField(max_length=50, null=True, blank=True)
    password = models.CharField(max_length=50, null=True, blank=True)
    api_key = models.CharField(max_length=255, null=True, blank=True)
    workspace_ref = models.URLField(False, null=True, blank=True)
    store_ref = models.URLField(null=True, blank=True)
    resources_ref = models.URLField(null = True, blank = True)
    profiles = models.ManyToManyField(settings.AUTH_USER_MODEL, through='ServiceProfileRole')
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    first_noanswer = models.DateTimeField(null=True, blank=True)
    noanswer_retries = models.PositiveIntegerField(null=True, blank=True)
    external_id = models.IntegerField(null=True, blank=True)
    parent = models.ForeignKey('services.Service', null=True, blank=True, related_name='service_set')

    # Supported Capabilities

    def __unicode__(self):
        return self.name

    @property
    def ptype(self):
        # Return the gxp ptype that should be used to display layers
        return GXP_PTYPES[self.type]

    def get_absolute_url(self):
        return '/services/%i' % self.id

    class Meta(ResourceBase.Meta):
        pass


class ServiceProfileRole(models.Model):
    """
    ServiceProfileRole is an intermediate model to bind Profiles and Services and apply roles.
    """
    profiles = models.ForeignKey(settings.AUTH_USER_MODEL)
    service = models.ForeignKey(Service)
    role = models.CharField(choices=ROLE_VALUES, max_length=255, help_text=_('function performed by the responsible party'))

class ServiceLayer(models.Model):
    service = models.ForeignKey(Service)
    layer = models.ForeignKey(Layer, null=True)
    typename = models.CharField(_("Layer Name"), max_length=255)
    title = models.CharField(_("Layer Title"), max_length=512)
    description = models.TextField(_("Layer Description"), null=True)
    styles = models.TextField(_("Layer Styles"), null=True)


class WebServiceHarvestLayersJob(models.Model):
    service = models.ForeignKey(Service, blank=False, null=False, unique=True)
    status = models.CharField(choices= [(x, x) for x in STATUS_VALUES], max_length=10, blank=False, null=False, default='pending')

class WebServiceRegistrationJob(models.Model):
    base_url = models.URLField(unique=True)
    type = models.CharField(max_length=4, choices=SERVICE_TYPES)
    status = models.CharField(choices= [(x, x) for x in STATUS_VALUES], max_length=10, blank=False, null=False, default='pending')

def post_save_service(instance, sender, created, **kwargs):
    if created:
        instance.set_default_permissions()

def pre_delete_service(instance, sender, **kwargs):
    for layer in instance.layer_set.all():
        layer.delete()
    # if instance.method == 'H':
    #     gn = Layer.objects.gn_catalog
    #     gn.control_harvesting_task('stop', [instance.external_id])
    #     gn.control_harvesting_task('remove', [instance.external_id])
    if instance.method == 'C':
        try:
            _user = settings.OGC_SERVER['default']['USER']
            _password = settings.OGC_SERVER['default']['PASSWORD']
            gs = Catalog(settings.OGC_SERVER['default']['LOCATION'] + "rest",
                          _user , _password)
            cascade_store = gs.get_store(instance.name, settings.CASCADE_WORKSPACE)
            gs.delete(cascade_store, recurse=True)
        except FailedRequestError:
            logger.error("Could not delete cascading WMS Store for %s - maybe already gone" % instance.name)



signals.pre_delete.connect(pre_delete_service, sender=Service)
signals.post_save.connect(post_save_service, sender=Service)
