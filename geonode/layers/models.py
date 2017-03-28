# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

import uuid
import logging

from datetime import datetime


from django.db import models
from django.db.models import signals
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.core.files.storage import FileSystemStorage

from geonode.base.models import ResourceBase, ResourceBaseManager, resourcebase_post_save
from geonode.people.utils import get_valid_user
from agon_ratings.models import OverallRating
from geonode.utils import check_shp_columnnames
from geonode.security.models import remove_object_permissions

logger = logging.getLogger("geonode.layers.models")

shp_exts = ['.shp', ]
csv_exts = ['.csv']
kml_exts = ['.kml']
vec_exts = shp_exts + csv_exts + kml_exts

cov_exts = ['.tif', '.tiff', '.geotiff', '.geotif']

TIME_REGEX = (
    ('[0-9]{8}', _('YYYYMMDD')),
    ('[0-9]{8}T[0-9]{6}', _("YYYYMMDD'T'hhmmss")),
    ('[0-9]{8}T[0-9]{6}Z', _("YYYYMMDD'T'hhmmss'Z'")),
)

TIME_REGEX_FORMAT = {
    '[0-9]{8}': '%Y%m%d',
    '[0-9]{8}T[0-9]{6}': '%Y%m%dT%H%M%S',
    '[0-9]{8}T[0-9]{6}Z': '%Y%m%dT%H%M%SZ'
}


class Style(models.Model):

    """Model for storing styles.
    """
    name = models.CharField(_('style name'), max_length=255, unique=True)
    sld_title = models.CharField(max_length=255, null=True, blank=True)
    sld_body = models.TextField(_('sld text'), null=True, blank=True)
    sld_version = models.CharField(
        _('sld version'),
        max_length=12,
        null=True,
        blank=True)
    sld_url = models.CharField(_('sld url'), null=True, max_length=1000)
    workspace = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return "%s" % self.name.encode('utf-8')

    def absolute_url(self):
        return self.sld_url.split(settings.OGC_SERVER['default']['LOCATION'], 1)[1]


class LayerManager(ResourceBaseManager):

    def __init__(self):
        models.Manager.__init__(self)


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
    typename = models.CharField(max_length=128, null=True, blank=True)

    is_mosaic = models.BooleanField(default=False)
    has_time = models.BooleanField(default=False)
    has_elevation = models.BooleanField(default=False)
    time_regex = models.CharField(max_length=128, null=True, blank=True, choices=TIME_REGEX)
    elevation_regex = models.CharField(max_length=128, null=True, blank=True)

    default_style = models.ForeignKey(
        Style,
        related_name='layer_default_style',
        null=True,
        blank=True)
    styles = models.ManyToManyField(Style, related_name='layer_styles')

    charset = models.CharField(max_length=255, default='UTF-8')

    upload_session = models.ForeignKey('UploadSession', blank=True, null=True)

    @property
    def is_remote(self):
        return self.storeType == "remoteStore"

    @property
    def service(self):
        """Get the related service object dynamically
        """
        service_layers = self.servicelayer_set.all()
        if len(service_layers) == 0:
            return None
        else:
            return service_layers[0].service

    def is_vector(self):
        return self.storeType == 'dataStore'

    @property
    def display_type(self):
        return ({
            "dataStore": "Vector Data",
            "coverageStore": "Raster Data",
        }).get(self.storeType, "Data")

    @property
    def data_model(self):
        if hasattr(self, 'modeldescription_set'):
            lmd = self.modeldescription_set.all()
            if lmd.exists():
                return lmd.get().get_django_model()

        return None

    @property
    def data_objects(self):
        if self.data_model is not None:
            return self.data_model.objects.using('datastore')

        return None

    @property
    def service_type(self):
        if self.storeType == 'coverageStore':
            return "WCS"
        if self.storeType == 'dataStore':
            return "WFS"

    @property
    def ows_url(self):
        if self.is_remote:
            return self.service.base_url
        else:
            return settings.OGC_SERVER['default']['PUBLIC_LOCATION'] + "wms"

    @property
    def ptype(self):
        if self.is_remote:
            return self.service.ptype
        else:
            return "gxp_wmscsource"

    @property
    def service_typename(self):
        if self.is_remote:
            return "%s:%s" % (self.service.name, self.typename)
        else:
            return self.typename

    @property
    def attributes(self):
        return self.attribute_set.exclude(attribute='the_geom')

    def get_base_file(self):
        """Get the shp or geotiff file for this layer.
        """

        # If there was no upload_session return None
        if self.upload_session is None:
            return None, None

        base_exts = [x.replace('.', '') for x in cov_exts + vec_exts]
        base_files = self.upload_session.layerfile_set.filter(
            name__in=base_exts)
        base_files_count = base_files.count()

        # If there are no files in the upload_session return None
        if base_files_count == 0:
            return None, None

        msg = 'There should only be one main file (.shp or .geotiff), found %s' % base_files_count
        assert base_files_count == 1, msg

        # we need to check, for shapefile, if column names are valid
        list_col = None
        if self.storeType == 'dataStore':
            valid_shp, wrong_column_name, list_col = check_shp_columnnames(self)
            if wrong_column_name:
                msg = 'Shapefile has an invalid column name: %s' % wrong_column_name
            else:
                msg = _('File cannot be opened, maybe check the encoding')
            assert valid_shp, msg

        # no error, let's return the base files
        return base_files.get(), list_col

    def get_absolute_url(self):
        return reverse('layer_detail', args=(self.service_typename,))

    def attribute_config(self):
        # Get custom attribute sort order and labels if any
        cfg = {}
        visible_attributes = self.attribute_set.visible()
        if (visible_attributes.count() > 0):
            cfg["getFeatureInfo"] = {
                "fields": [l.attribute for l in visible_attributes],
                "propertyNames": dict([(l.attribute, l.attribute_label) for l in visible_attributes])
            }
        return cfg

    def __str__(self):
        if self.typename is not None:
            return "%s Layer" % self.service_typename.encode('utf-8')
        elif self.name is not None:
            return "%s Layer" % self.name
        else:
            return "Unamed Layer"

    class Meta:
        # custom permissions,
        # change and delete are standard in django-guardian
        permissions = (
            ('change_layer_data', 'Can edit layer data'),
            ('change_layer_style', 'Can change layer style'),
        )

    # Permission Level Constants
    # LEVEL_NONE inherited
    LEVEL_READ = 'layer_readonly'
    LEVEL_WRITE = 'layer_readwrite'
    LEVEL_ADMIN = 'layer_admin'

    def maps(self):
        from geonode.maps.models import MapLayer
        return MapLayer.objects.filter(name=self.typename)

    @property
    def class_name(self):
        return self.__class__.__name__

    @property
    def geogig_enabled(self):
        return (len(self.link_set.geogig()) > 0)

    @property
    def geogig_link(self):
        if(self.geogig_enabled):
            return getattr(self.link_set.filter(name__icontains='clone in geogig').first(), 'url', None)
        return None


class UploadSession(models.Model):

    """Helper class to keep track of uploads.
    """
    date = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    processed = models.BooleanField(default=False)
    error = models.TextField(blank=True, null=True)
    traceback = models.TextField(blank=True, null=True)
    context = models.TextField(blank=True, null=True)

    def successful(self):
        return self.processed and self.errors is None


class LayerFile(models.Model):

    """Helper class to store original files.
    """
    upload_session = models.ForeignKey(UploadSession)
    name = models.CharField(max_length=255)
    base = models.BooleanField(default=False)
    file = models.FileField(upload_to='layers',
                            storage=FileSystemStorage(base_url=settings.LOCAL_MEDIA_URL),  max_length=255)


class AttributeManager(models.Manager):

    """Helper class to access filtered attributes
    """

    def visible(self):
        return self.get_queryset().filter(
            visible=True).order_by('display_order')


class Attribute(models.Model):

    """
        Auxiliary model for storing layer attributes.

       This helps reduce the need for runtime lookups
       to other servers, and lets users customize attribute titles,
       sort order, and visibility.
    """
    layer = models.ForeignKey(
        Layer,
        blank=False,
        null=False,
        unique=False,
        related_name='attribute_set')
    attribute = models.CharField(
        _('attribute name'),
        help_text=_('name of attribute as stored in shapefile/spatial database'),
        max_length=255,
        blank=False,
        null=True,
        unique=False)
    description = models.CharField(
        _('attribute description'),
        help_text=_('description of attribute to be used in metadata'),
        max_length=255,
        blank=True,
        null=True)
    attribute_label = models.CharField(
        _('attribute label'),
        help_text=_('title of attribute as displayed in GeoNode'),
        max_length=255,
        blank=True,
        null=True,
        unique=False)
    attribute_type = models.CharField(
        _('attribute type'),
        help_text=_('the data type of the attribute (integer, string, geometry, etc)'),
        max_length=50,
        blank=False,
        null=False,
        default='xsd:string',
        unique=False)
    visible = models.BooleanField(
        _('visible?'),
        help_text=_('specifies if the attribute should be displayed in identify results'),
        default=True)
    display_order = models.IntegerField(
        _('display order'),
        help_text=_('specifies the order in which attribute should be displayed in identify results'),
        default=1)

    # statistical derivations
    count = models.IntegerField(
        _('count'),
        help_text=_('count value for this field'),
        default=1)
    min = models.CharField(
        _('min'),
        help_text=_('minimum value for this field'),
        max_length=255,
        blank=False,
        null=True,
        unique=False,
        default='NA')
    max = models.CharField(
        _('max'),
        help_text=_('maximum value for this field'),
        max_length=255,
        blank=False,
        null=True,
        unique=False,
        default='NA')
    average = models.CharField(
        _('average'),
        help_text=_('average value for this field'),
        max_length=255,
        blank=False,
        null=True,
        unique=False,
        default='NA')
    median = models.CharField(
        _('median'),
        help_text=_('median value for this field'),
        max_length=255,
        blank=False,
        null=True,
        unique=False,
        default='NA')
    stddev = models.CharField(
        _('standard deviation'),
        help_text=_('standard deviation for this field'),
        max_length=255,
        blank=False,
        null=True,
        unique=False,
        default='NA')
    sum = models.CharField(
        _('sum'),
        help_text=_('sum value for this field'),
        max_length=255,
        blank=False,
        null=True,
        unique=False,
        default='NA')
    unique_values = models.TextField(
        _('unique values for this field'),
        null=True,
        blank=True,
        default='NA')
    last_stats_updated = models.DateTimeField(
        _('last modified'),
        default=datetime.now,
        help_text=_('date when attribute statistics were last updated'))  # passing the method itself, not

    objects = AttributeManager()

    def __str__(self):
        return "%s" % self.attribute_label.encode(
            "utf-8") if self.attribute_label else self.attribute.encode("utf-8")

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
        instance.abstract = unicode(_('No abstract provided'))
    if instance.title == '' or instance.title is None:
        instance.title = instance.name

    # Set a default user for accountstream to work correctly.
    if instance.owner is None:
        instance.owner = get_valid_user()

    if instance.uuid == '':
        instance.uuid = str(uuid.uuid1())

    if instance.typename is None:
        # Set a sensible default for the typename
        instance.typename = 'geonode:%s' % instance.name

    base_file, info = instance.get_base_file()

    if info:
        instance.info = info

    if base_file is not None:
        extension = '.%s' % base_file.name
        if extension in vec_exts:
            instance.storeType = 'dataStore'
        elif extension in cov_exts:
            instance.storeType = 'coverageStore'

    # Set sane defaults for None in bbox fields.
    if instance.bbox_x0 is None:
        instance.bbox_x0 = -180

    if instance.bbox_x1 is None:
        instance.bbox_x1 = 180

    if instance.bbox_y0 is None:
        instance.bbox_y0 = -90

    if instance.bbox_y1 is None:
        instance.bbox_y1 = 90

    bbox = [
        instance.bbox_x0,
        instance.bbox_x1,
        instance.bbox_y0,
        instance.bbox_y1]

    instance.set_bounds_from_bbox(bbox)


def pre_delete_layer(instance, sender, **kwargs):
    """
    Remove any associated style to the layer, if it is not used by other layers.
    Default style will be deleted in post_delete_layer
    """
    if instance.is_remote:
        # we need to delete the maplayers here because in the post save layer.service is not available anymore
        # REFACTOR
        from geonode.maps.models import MapLayer
        if instance.typename:
            logger.debug(
                "Going to delete associated maplayers for [%s]",
                instance.typename.encode('utf-8'))
            MapLayer.objects.filter(
                name=instance.typename,
                ows_url=instance.ows_url).delete()
        return

    logger.debug(
        "Going to delete the styles associated for [%s]",
        instance.typename.encode('utf-8'))
    ct = ContentType.objects.get_for_model(instance)
    OverallRating.objects.filter(
        content_type=ct,
        object_id=instance.id).delete()
    default_style = instance.default_style
    for style in instance.styles.all():
        if style.layer_styles.all().count() == 1:
            if style != default_style:
                style.delete()

    # Delete object permissions
    remove_object_permissions(instance)


def post_delete_layer(instance, sender, **kwargs):
    """
    Removed the layer from any associated map, if any.
    Remove the layer default style.
    """
    if instance.is_remote:
        return

    from geonode.maps.models import MapLayer
    if instance.typename:
        logger.debug(
            "Going to delete associated maplayers for [%s]",
            instance.typename.encode('utf-8'))
        MapLayer.objects.filter(
            name=instance.typename,
            ows_url=instance.ows_url).delete()

    if instance.typename:
        logger.debug(
            "Going to delete the default style for [%s]",
            instance.typename.encode('utf-8'))

    if instance.default_style and Layer.objects.filter(
            default_style__id=instance.default_style.id).count() == 0:
        instance.default_style.delete()

    try:
        if instance.upload_session:
            for lf in instance.upload_session.layerfile_set.all():
                lf.file.delete()
    except UploadSession.DoesNotExist:
        pass


signals.pre_save.connect(pre_save_layer, sender=Layer)
signals.post_save.connect(resourcebase_post_save, sender=Layer)
signals.pre_delete.connect(pre_delete_layer, sender=Layer)
signals.post_delete.connect(post_delete_layer, sender=Layer)
