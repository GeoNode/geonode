import re

from django.conf import settings
from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _

from geonode.layers.models import Layer, Attribute
from geonode.maps.models import Map
from geonode.people.models import Profile

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

    def update_gazetteer(self):
        from geonode.contrib.worldmap.gazetteer.utils import add_to_gazetteer, delete_from_gazetteer
        if not self.in_gazetteer:
            delete_from_gazetteer(self.name)
        else:
            includedAttributes = []
            # from geonode.contrib.worldmap.gazetteer.models import GazetteerAttribute
            for attribute in self.layer.attribute_set.all():
                if hasattr(attribute, 'gazetteerattribute'):
                    if attribute.gazetteerattribute.in_gazetteer:
                        includedAttributes.append(attribute.attribute)

            print includedAttributes

            # includedAttributes = []
            # gazetteerAttributes = self.attribute_set.filter(in_gazetteer=True)
            # for attribute in gazetteerAttributes:
            #     includedAttributes.append(attribute.attribute)

            # TODO implement this
            startAttribute = None
            endAttribute = None
            # startAttribute = self.attribute_set.filter(
            #    is_gaz_start_date=True)[0].attribute if
            #    self.attribute_set.filter(is_gaz_start_date=True).exists() > 0
            # else None
            # endAttribute = self.attribute_set.filter(
            #   is_gaz_end_date=True)[0].attribute if
            # self.attribute_set.filter(is_gaz_end_date=True).exists() > 0 else None

            add_to_gazetteer(self.layer.name,
                             includedAttributes,
                             start_attribute=startAttribute,
                             end_attribute=endAttribute,
                             project=self.gazetteer_project,
                             user=self.layer.owner.username)


class ExtLayerAttribute(models.Model):
    attribute = models.OneToOneField(
        Attribute,
        blank=False,
        null=False)
    searchable = models.BooleanField(default=False)

    def layer_name(self):
        return self.attribute.layer.name


class ExtMap(models.Model):
    map = models.OneToOneField(Map)
    content_map = models.TextField(_('Site Content'), blank=True, null=True, default=settings.DEFAULT_MAP_ABSTRACT)
    group_params = models.TextField(_('Layer Category Parameters'), blank=True)


class MapStats(models.Model):
    map = models.OneToOneField(Map)
    visits = models.IntegerField(_("Visits"), default=0)
    uniques = models.IntegerField(_("Unique Visitors"), default=0)
    last_modified = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name_plural = 'Map stats'


class LayerStats(models.Model):
    layer = models.OneToOneField(Layer)
    visits = models.IntegerField(_("Visits"), default=0)
    uniques = models.IntegerField(_("Unique Visitors"), default=0)
    downloads = models.IntegerField(_("Downloads"), default=0)
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
