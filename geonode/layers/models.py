# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
from urlparse import urlparse, urljoin

import httplib2
import urllib
import logging

from datetime import datetime
from lxml import etree

from django.conf import settings
from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.urlresolvers import reverse

from geonode import GeoNodeException
from geonode.base.models import ResourceBase, ResourceBaseManager, Link, \
    resourcebase_post_save, resourcebase_post_delete
from geonode.people.models import Profile
from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.layers.enumerations import LAYER_ATTRIBUTE_NUMERIC_DATA_TYPES
from geonode.utils import http_client
from agon_ratings.models import OverallRating

logger = logging.getLogger("geonode.layers.models")


class Style(models.Model):
    """Model for storing styles.
    """
    name = models.CharField(_('style name'), max_length=255, unique=True)
    sld_title = models.CharField(max_length=255, null=True, blank=True)
    sld_body = models.TextField(_('sld text'), null=True, blank=True)
    sld_version = models.CharField(_('sld version'), max_length=12, null=True, blank=True)
    sld_url = models.CharField(_('sld url'), null = True, max_length=1000)
    workspace = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return "%s" % self.name.encode('utf-8')

class LayerManager(ResourceBaseManager):

    def __init__(self):
        models.Manager.__init__(self)

        
def add_bbox_query(q, bbox):
    '''modify the queryset q to limit to the provided bbox

    bbox - 4 tuple of floats representing x0,x1,y0,y1
    returns the modified query
    '''
    bbox = map(str, bbox) # 2.6 compat - float to decimal conversion
    q = q.filter(bbox_x0__gte=bbox[0])
    q = q.filter(bbox_x1__lte=bbox[1])
    q = q.filter(bbox_y0__gte=bbox[2])
    return q.filter(bbox_y1__lte=bbox[3])


class Layer(ResourceBase):
    """
    Layer (inherits ResourceBase fields)
    """

    # internal fields
    objects = LayerManager()
    workspace = models.CharField(max_length=128)
    store = models.CharField(max_length=128)
    storeType = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    typename = models.CharField(max_length=128, unique=True)

    popular_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)

    default_style = models.ForeignKey(Style, related_name='layer_default_style', null=True, blank=True)
    styles = models.ManyToManyField(Style, related_name='layer_styles')

    def is_vector(self):
        return self.storeType == 'dataStore'

    @property
    def display_type(self):
        return ({
            "dataStore" : "Vector Data",
            "coverageStore": "Raster Data",
        }).get(self.storeType, "Data")

    @property
    def service_type(self):
        if self.storeType == 'coverageStore':
            return "WCS"
        if self.storeType == 'dataStore':
            return "WFS"

    def get_absolute_url(self):
        return reverse('layer_detail', args=(self.typename,))

    def attribute_config(self):
        #Get custom attribute sort order and labels if any
            cfg = {}
            visible_attributes =  self.attribute_set.visible()
            if (visible_attributes.count() > 0):
                cfg["getFeatureInfo"] = {
                    "fields":  [l.attribute for l in visible_attributes],
                    "propertyNames":   dict([(l.attribute,l.attribute_label) for l in visible_attributes])
                }
            return cfg

    def __str__(self):
        return "%s Layer" % self.typename.encode('utf-8')

    class Meta:
        # custom permissions,
        # change and delete are standard in django
        permissions = (('view_layer', 'Can view'),
                       ('change_layer_permissions', "Can change permissions"), )

    # Permission Level Constants
    # LEVEL_NONE inherited
    LEVEL_READ  = 'layer_readonly'
    LEVEL_WRITE = 'layer_readwrite'
    LEVEL_ADMIN = 'layer_admin'

    def tiles_url(self):
        return self.link_set.get(name='Tiles').url

    def ows_url(self):
        ows_url = None
        if self.link_set.filter(name='OWS').count() > 0:
            ows_url = self.link_set.get(name='OWS').url
        return ows_url

    def get_thumbnail_url(self):
        try:
            return self.thumbnail.thumb_file.url
        except:
            return None

    def maps(self):
        from geonode.maps.models import MapLayer
        return  MapLayer.objects.filter(name=self.typename)

    @property
    def class_name(self):
        return self.__class__.__name__

class Layer_Styles(models.Model):
    layer = models.ForeignKey(Layer)
    style = models.ForeignKey(Style)

class AttributeManager(models.Manager):
    """Helper class to access filtered attributes
    """

    def visible(self):
       return self.get_query_set().filter(visible=True).order_by('display_order')


class Attribute(models.Model):
    """
        Auxiliary model for storing layer attributes.

       This helps reduce the need for runtime lookups
       to other servers, and lets users customize attribute titles,
       sort order, and visibility.
    """
    layer = models.ForeignKey(Layer, blank=False, null=False, unique=False, related_name='attribute_set')
    attribute = models.CharField(_('attribute name'), help_text=_('name of attribute as stored in shapefile/spatial database'), max_length=255, blank=False, null=True, unique=False)
    description = models.CharField(_('attribute description'), help_text=_('description of attribute to be used in metadata'), max_length=255, blank=True, null=True)
    attribute_label = models.CharField(_('attribute label'), help_text=_('title of attribute as displayed in GeoNode'), max_length=255, blank=False, null=True, unique=False)
    attribute_type = models.CharField(_('attribute type'), help_text=_('the data type of the attribute (integer, string, geometry, etc)'), max_length=50, blank=False, null=False, default='xsd:string', unique=False)
    visible = models.BooleanField(_('visible?'), help_text=_('specifies if the attribute should be displayed in identify results'), default=True)
    display_order = models.IntegerField(_('display order'), help_text=_('specifies the order in which attribute should be displayed in identify results'), default=1)

    # statistical derivations
    count = models.IntegerField(_('count'), help_text=_('count value for this field'), default=1)
    min = models.CharField(_('min'), help_text=_('minimum value for this field'), max_length=255, blank=False, null=True, unique=False, default='NA')
    max = models.CharField(_('max'), help_text=_('maximum value for this field'), max_length=255, blank=False, null=True, unique=False, default='NA')
    average = models.CharField(_('average'), help_text=_('average value for this field'), max_length=255, blank=False, null=True, unique=False, default='NA')
    median = models.CharField(_('median'), help_text=_('median value for this field'), max_length=255, blank=False, null=True, unique=False, default='NA')
    stddev = models.CharField(_('standard deviation'), help_text=_('standard deviation for this field'), max_length=255, blank=False, null=True, unique=False, default='NA')
    sum = models.CharField(_('sum'), help_text=_('sum value for this field'), max_length=255, blank=False, null=True, unique=False, default='NA')
    unique_values = models.TextField(_('unique values for this field'), null=True, blank=True, default='NA')
    last_stats_updated = models.DateTimeField(_('last modified'), default=datetime.now, help_text=_('date when attribute statistics were last updated')) # passing the method itself, not

    objects = AttributeManager()

    def __str__(self):
        return "%s" % self.attribute_label.encode("utf-8") if self.attribute_label else self.attribute.encode("utf-8")

    def unique_values_as_list(self):
        return self.unique_values.split(',')


def pre_save_layer(instance, sender, **kwargs):
    if kwargs.get('raw', False):
        instance.owner = instance.resourcebase_ptr.owner
        instance.uuid = instance.resourcebase_ptr.uuid
        instance.bbox_x0 = instance.resourcebase_ptr.bbox_x0
        instance.bbox_x1 = instance.resourcebase_ptr.bbox_x1
        instance.bbox_y0 = instance.resourcebase_ptr.bbox_y0
        instance.bbox_y1 = instance.resourcebase_ptr.bbox_y1

    if instance.abstract == '' or instance.abstract is None:
        instance.abstract = 'No abstract provided'
    if instance.title == '' or instance.title is None:
        instance.title = instance.name

def pre_delete_layer(instance, sender, **kwargs):
    """
    Remove any associated style to the layer, if it is not used by other layers.
    Default style will be deleted in post_delete_layer
    """
    logger.debug("Going to delete the styles associated for [%s]", instance.typename.encode('utf-8'))
    ct = ContentType.objects.get_for_model(instance)
    OverallRating.objects.filter(content_type = ct, object_id = instance.id).delete()
    default_style = instance.default_style
    for style in instance.styles.all():
        if style.layer_styles.all().count()==1:
            if style != default_style:
                style.delete()

def post_delete_layer(instance, sender, **kwargs):
    """
    Removed the layer from any associated map, if any.
    Remove the layer default style.
    """
    from geonode.maps.models import MapLayer
    logger.debug("Going to delete associated maplayers for [%s]", instance.typename.encode('utf-8'))
    MapLayer.objects.filter(name=instance.typename).delete()
    logger.debug("Going to delete the default style for [%s]", instance.typename.encode('utf-8'))

    if instance.default_style and Layer.objects.filter(default_style__id=instance.default_style.id).count() == 0:
        instance.default_style.delete()


signals.pre_save.connect(pre_save_layer, sender=Layer)
signals.pre_delete.connect(pre_delete_layer, sender=Layer)
signals.post_delete.connect(post_delete_layer, sender=Layer)
signals.post_save.connect(resourcebase_post_save, sender=Layer)
signals.post_delete.connect(resourcebase_post_delete, sender=Layer)
