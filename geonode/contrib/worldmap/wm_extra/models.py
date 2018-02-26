import re
import urllib
import urlparse

from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _
from django.db.models import signals

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.people.models import Profile

from .encode import despam, XssCleaner
from .signals import save_profile, add_ext_layer, add_ext_map

try:
    from django.utils import timezone
    now = timezone.now
except ImportError:
    from datetime import datetime
    now = datetime.now


ACTION_TYPES = [
    ['layer_delete', 'Layer Deleted'],
    ['layer_create', 'Layer Created'],
    ['layer_upload', 'Layer Uploaded'],
    ['map_delete', 'Map Deleted'],
    ['map_create', 'Map Created'],
]


ows_sub = re.compile(r"[&\?]+SERVICE=WMS|[&\?]+REQUEST=GetCapabilities", re.IGNORECASE)
DEFAULT_CONTENT=_(
    '<h3>The Harvard WorldMap Project</h3>\
  <p>WorldMap is an open source web mapping system that is currently\
  under construction. It is built to assist academic research and\
  teaching as well as the general public and supports discovery,\
  investigation, analysis, visualization, communication and archiving\
  of multi-disciplinary, multi-source and multi-format data,\
  organized spatially and temporally.</p>\
  <p>The first instance of WorldMap, focused on the continent of\
  Africa, is called AfricaMap. Since its beta release in November of\
  2008, the framework has been implemented in several geographic\
  locations with different research foci, including metro Boston,\
  East Asia, Vermont, Harvard Forest and the city of Paris. These web\
  mapping applications are used in courses as well as by individual\
  researchers.</p>\
  <h3>Introduction to the WorldMap Project</h3>\
  <p>WorldMap solves the problem of discovering where things happen.\
  It draws together an array of public maps and scholarly data to\
  create a common source where users can:</p>\
  <ol>\
  <li>Interact with the best available public data for a\
  city/region/continent</li>\
  <li>See the whole of that area yet also zoom in to particular\
  places</li>\
  <li>Accumulate both contemporary and historical data supplied by\
  researchers and make it permanently accessible online</li>\
  <li>Work collaboratively across disciplines and organizations with\
  spatial information in an online environment</li>\
  </ol>\
  <p>The WorldMap project aims to accomplish these goals in stages,\
  with public and private support. It draws on the basic insight of\
  geographic information systems that spatiotemporal data becomes\
  more meaningful as more "layers" are added, and makes use of tiling\
  and indexing approaches to facilitate rapid search and\
  visualization of large volumes of disparate data.</p>\
  <p>WorldMap aims to augment existing initiatives for globally\
  sharing spatial data and technology such as <a target="_blank" href="http://www.gsdi.org/">GSDI</a> (Global Spatial Data\
  Infrastructure).WorldMap makes use of <a target="_blank" href="http://www.opengeospatial.org/">OGC</a> (Open Geospatial\
  Consortium) compliant web services such as <a target="_blank" href="http://en.wikipedia.org/wiki/Web_Map_Service">WMS</a> (Web\
  Map Service), emerging open standards such as <a target="_blank" href="http://wiki.osgeo.org/wiki/Tile_Map_Service_Specification">WMS-C</a>\
  (cached WMS), and standards-based metadata formats, to enable\
  WorldMap data layers to be inserted into existing data\
  infrastructures.&nbsp;<br>\
  <br>\
  All WorldMap source code will be made available as <a target="_blank" href="http://www.opensource.org/">Open Source</a> for others to use\
  and improve upon.</p>'
)

class ExtLayer(models.Model):
    layer = models.OneToOneField(Layer)
    in_gazetteer = models.BooleanField(_('In Gazetteer?'), blank=False, null=False, default=False)
    gazetteer_project = models.CharField(_("Gazetteer Project"), max_length=128, blank=True, null=True)
    searchable = models.BooleanField(_('Searchable?'), default=False)
    created_dttm = models.DateTimeField(auto_now_add=True)
    date_format = models.CharField(_('Date Format'), max_length=255, blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)
    in_gazetteer = models.BooleanField(_('In Gazetteer?'), default=False)
    is_gaz_start_date = models.BooleanField(_('Gazetteer Start Date'), default=False)
    is_gaz_end_date = models.BooleanField(_('Gazetteer End Date'), default=False)

    # join target: available only for layers within the DATAVERSE_DB
    # def add_as_join_target(self):
    #     if not self.id:
    #         return 'n/a'
    #     if self.store != settings.DB_DATAVERSE_NAME:
    #         return 'n/a'
    #     admin_url = reverse('admin:datatables_jointarget_add', args=())
    #     add_as_target_link = '%s?layer=%s' % (admin_url, self.id)
    #     return '<a href="%s">Add as Join Target</a>' % (add_as_target_link)
    # add_as_join_target.allow_tags = True
    #
    # @property
    # def is_remote(self):
    #     return self.storeType == "remoteStore"
    #
    # @property
    # def service(self):
    #     """Get the related service object dynamically
    #     """
    #     service_layers = self.servicelayer_set.all()
    #     if len(service_layers) == 0:
    #         return None
    #     else:
    #         return service_layers[0].service
    #
    # def queue_gazetteer_update(self):
    #     from geonode.queue.models import GazetteerUpdateJob
    #     if GazetteerUpdateJob.objects.filter(layer=self.id).exists() == 0:
    #         newJob = GazetteerUpdateJob(layer=self)
    #         newJob.save()
    #
    # def update_gazetteer(self):
    #     from geonode.gazetteer.utils import add_to_gazetteer, delete_from_gazetteer
    #     if not self.in_gazetteer:
    #         delete_from_gazetteer(self.name)
    #     else:
    #         includedAttributes = []
    #         gazetteerAttributes = self.attribute_set.filter(in_gazetteer=True)
    #         for attribute in gazetteerAttributes:
    #             includedAttributes.append(attribute.attribute)
    #
    #         startAttribute = self.attribute_set.filter(is_gaz_start_date=True)[0].attribute if self.attribute_set.filter(is_gaz_start_date=True).exists() > 0 else None
    #         endAttribute = self.attribute_set.filter(is_gaz_end_date=True)[0].attribute if self.attribute_set.filter(is_gaz_end_date=True).exists() > 0 else None
    #
    #         add_to_gazetteer(self.name,
    #                          includedAttributes,
    #                          start_attribute=startAttribute,
    #                          end_attribute=endAttribute,
    #                          project=self.gazetteer_project,
    #                          user=self.owner.username)

    # this must be added in a pre-delete signal
    # if settings.USE_GAZETTEER and instance.in_gazetteer:
    #     instance.in_gazetteer = False
    #     instance.update_gazetteer()


class ExtMap(models.Model):
    map = models.OneToOneField(Map)
    content_map = models.TextField(_('Site Content'), blank=True, null=True, default=DEFAULT_CONTENT)


class MapStats(models.Model):
    map = models.OneToOneField(Map)
    visits = models.IntegerField(_("Visits"), default= 0)
    uniques = models.IntegerField(_("Unique Visitors"), default = 0)
    last_modified = models.DateTimeField(auto_now=True,null=True)

    class Meta:
        verbose_name_plural = 'Map stats'


class LayerStats(models.Model):
    layer = models.OneToOneField(Layer)
    visits = models.IntegerField(_("Visits"), default = 0)
    uniques = models.IntegerField(_("Unique Visitors"), default = 0)
    downloads = models.IntegerField(_("Downloads"), default = 0)
    last_modified = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name_plural = 'Layer stats'


class Endpoint(models.Model):
    """
    Model for a remote endpoint.
    """
    description = models.TextField(_('Describe Map Service'))
    url = models.URLField(_('Map service URL'))
    owner = models.ForeignKey(Profile, blank=True, null=True)


class Action(models.Model):
    """
    Model to store user actions, such a layer creation or deletion.
    """
    action_type = models.CharField(max_length=25, choices=ACTION_TYPES)
    description = models.CharField(max_length=255, db_index=True)
    args = models.CharField(max_length=255, db_index=True)
    timestamp = models.DateTimeField(default=now, db_index=True)


# signals for adding actions

def action_add_layer(instance, sender, created, **kwargs):
    if created:
        username = instance.owner.username
        action = Action(
                        action_type='layer_create',
                        description='User %s created layer with id %s' % (username, instance.id),
                        args=instance.uuid,
                        )
        action.save()

def action_delete_layer(instance, sender, **kwargs):
    username = instance.owner.username
    action = Action(
                    action_type='layer_delete',
                    description='User %s deleted layer with id %s' % (username, instance.id),
                    args=instance.uuid,
                    )
    action.save()

def action_add_map(instance, sender, created, **kwargs):
    if created:
        username = instance.owner.username
        action = Action(
                        action_type='map_create',
                        description='User %s created map with id %s' % (username, instance.id),
                        args=instance.uuid,
                        )
        action.save()

def action_delete_map(instance, sender, **kwargs):
    username = instance.owner.username
    action = Action(
                    action_type='map_delete',
                    description='User %s deleted map with id %s' % (username, instance.id),
                    args=instance.uuid,
                    )
    action.save()

signals.post_save.connect(action_add_layer, sender=Layer)
signals.post_delete.connect(action_delete_layer, sender=Layer)
signals.post_save.connect(action_add_map, sender=Map)
signals.post_delete.connect(action_delete_map, sender=Map)
