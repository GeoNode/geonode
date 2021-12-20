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
import re
import logging

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.functional import classproperty
from django.utils.translation import ugettext_lazy as _

from tinymce.models import HTMLField

from geonode.client.hooks import hookset
from geonode.utils import check_shp_columnnames
from geonode.security.models import PermissionLevelMixin
from geonode.groups.conf import settings as groups_settings
from geonode.security.permissions import (
    VIEW_PERMISSIONS,
    OWNER_PERMISSIONS,
    DOWNLOAD_PERMISSIONS,
    DATASET_ADMIN_PERMISSIONS)
from geonode.base.models import (
    ResourceBase,
    ResourceBaseManager)

logger = logging.getLogger("geonode.layers.models")

shp_exts = ['.shp', ]
csv_exts = ['.csv']
kml_exts = ['.kml']
vec_exts = shp_exts + csv_exts + kml_exts
cov_exts = ['.tif', '.tiff', '.geotiff', '.geotif', '.asc']

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


class Style(models.Model, PermissionLevelMixin):

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
        return str(self.name)

    def absolute_url(self):
        if self.sld_url:
            if self.sld_url.startswith(
                    settings.OGC_SERVER['default']['LOCATION']):
                return self.sld_url.split(
                    settings.OGC_SERVER['default']['LOCATION'], 1)[1]
            elif self.sld_url.startswith(settings.OGC_SERVER['default']['PUBLIC_LOCATION']):
                return self.sld_url.split(
                    settings.OGC_SERVER['default']['PUBLIC_LOCATION'], 1)[1]

            return self.sld_url
        else:
            logger.error(
                f"SLD URL is empty for Style {self.name}")
            return None

    def get_self_resource(self):
        """Get associated resource base."""
        # Associate this model with resource
        try:
            dataset = self.dataset_styles.first()
            """:type: Dataset"""
            return dataset.get_self_resource()
        except Exception:
            return None


class DatasetManager(ResourceBaseManager):

    def __init__(self):
        models.Manager.__init__(self)


class Dataset(ResourceBase):

    """
    Dataset (inherits ResourceBase fields)
    """

    PERMISSIONS = {
        'write': [
            'change_dataset_data',
            'change_dataset_style',
        ]
    }

    # internal fields
    objects = DatasetManager()
    workspace = models.CharField(_('Workspace'), max_length=128)
    store = models.CharField(_('Store'), max_length=128)
    name = models.CharField(_('Name'), max_length=128)
    typename = models.CharField(_('Typename'), max_length=128, null=True, blank=True)
    ows_url = models.URLField(
        _('ows URL'),
        null=True,
        blank=True,
        help_text=_('The URL of the OWS service providing this layer, if any exists.'))

    is_mosaic = models.BooleanField(_('Is mosaic?'), default=False)
    has_time = models.BooleanField(_('Has time?'), default=False)
    has_elevation = models.BooleanField(_('Has elevation?'), default=False)
    time_regex = models.CharField(
        _('Time regex'),
        max_length=128,
        null=True,
        blank=True,
        choices=TIME_REGEX)
    elevation_regex = models.CharField(_('Elevation regex'), max_length=128, null=True, blank=True)

    ptype = models.CharField(
        _('P-Type'),
        null=False,
        blank=False,
        max_length=80,
        default="gxp_wmscsource")

    default_style = models.ForeignKey(
        Style,
        on_delete=models.SET_NULL,
        related_name='dataset_default_style',
        null=True,
        blank=True)

    styles = models.ManyToManyField(Style, related_name='dataset_styles')

    remote_service = models.ForeignKey("services.Service", null=True, blank=True, on_delete=models.CASCADE)

    charset = models.CharField(max_length=255, default='UTF-8')

    use_featureinfo_custom_template = models.BooleanField(
        _('use featureinfo custom template?'),
        help_text=_('specifies wether or not use a custom GetFeatureInfo template.'),
        default=False
    )
    featureinfo_custom_template = HTMLField(
        _('featureinfo custom template'),
        help_text=_('the custom GetFeatureInfo template HTML contents.'),
        unique=False,
        blank=True,
        null=True)

    def is_vector(self):
        return self.subtype == 'vector'

    @property
    def display_type(self):
        if self.subtype == "vector":
            return "Vector Data"
        elif self.subtype == "raster":
            return "Raster Data"
        else:
            return "Data"

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
    def attributes(self):
        if self.attribute_set and self.attribute_set.count():
            _attrs = self.attribute_set
        else:
            _attrs = Attribute.objects.filter(dataset=self)
        return _attrs.exclude(attribute='the_geom').order_by('display_order')

    @property
    def service_typename(self):
        return f"{self.remote_typename}:{self.alternate}" if self.remote_typename else self.alternate

    # layer geometry type.
    @property
    def gtype(self):
        # return attribute type without 'gml:' and 'PropertyType'
        if self.attribute_set and self.attribute_set.count():
            _attrs = self.attribute_set
        else:
            _attrs = Attribute.objects.filter(dataset=self)
        if _attrs.filter(attribute='the_geom').exists():
            _att_type = _attrs.filter(attribute='the_geom').first().attribute_type
            _gtype = re.match(r'\(\'gml:(.*?)\',', _att_type)
            return _gtype.group(1) if _gtype else None
        return None

    def get_base_file(self):
        """Get the shp or geotiff file for this layer.
        """

        # If there was no upload_session return None
        try:
            if self.upload_session is None:
                return None, None
        except Exception:
            return None, None

        base_exts = [x.replace('.', '') for x in cov_exts + vec_exts]
        base_files = self.upload_session.layerfile_set.filter(
            name__in=base_exts)
        base_files_count = base_files.count()

        # If there are no files in the upload_session return None
        if base_files_count == 0:
            return None, None

        msg = f'There should only be one main file (.shp or .geotiff or .asc), found {base_files_count}'
        assert base_files_count == 1, msg

        # we need to check, for shapefile, if column names are valid
        list_col = None
        if self.subtype == 'vector':
            valid_shp, wrong_column_name, list_col = check_shp_columnnames(
                self)
            if wrong_column_name:
                msg = f'Shapefile has an invalid column name: {wrong_column_name}'
            else:
                msg = _('File cannot be opened, maybe check the encoding')
            # AF: Removing assertion since if the original file does not exists anymore
            #     it won't be possible to update Metadata anymore
            # assert valid_shp, msg

        # no error, let's return the base files
        return base_files.get(), list_col

    def get_absolute_url(self):
        return hookset.dataset_detail_url(self)

    @property
    def embed_url(self):
        return reverse('dataset_embed', kwargs={'layername': self.service_typename})

    def attribute_config(self):
        # Get custom attribute sort order and labels if any
        cfg = {}
        visible_attributes = self.attribute_set.visible()
        if (visible_attributes.count() > 0):
            cfg["getFeatureInfo"] = {
                "fields": [lyr.attribute for lyr in visible_attributes],
                "propertyNames": {lyr.attribute: lyr.attribute_label for lyr in visible_attributes},
                "displayTypes": {lyr.attribute: lyr.featureinfo_type for lyr in visible_attributes}
            }

        if self.use_featureinfo_custom_template:
            cfg["ftInfoTemplate"] = self.featureinfo_custom_template

        return cfg

    def __str__(self):
        return str(self.alternate)

    class Meta(ResourceBase.Meta):
        # custom permissions,
        # change and delete are standard in django-guardian
        permissions = (
            ('change_dataset_data', 'Can edit layer data'),
            ('change_dataset_style', 'Can change layer style'),
        )

    # Permission Level Constants
    # LEVEL_NONE inherited
    LEVEL_READ = 'dataset_readonly'
    LEVEL_WRITE = 'dataset_readwrite'
    LEVEL_ADMIN = 'dataset_admin'

    @property
    def maps(self):
        from geonode.maps.models import Map
        map_ids = list(self.maplayers.values_list('map__id', flat=True))
        return Map.objects.filter(id__in=map_ids)

    @property
    def maplayers(self):
        from geonode.maps.models import MapLayer
        return MapLayer.objects.filter(name=self.alternate)

    @classproperty
    def allowed_permissions(cls):
        return {
            "anonymous": VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS,
            "default": OWNER_PERMISSIONS + DOWNLOAD_PERMISSIONS + DATASET_ADMIN_PERMISSIONS,
            groups_settings.REGISTERED_MEMBERS_GROUP_NAME: OWNER_PERMISSIONS + DOWNLOAD_PERMISSIONS + DATASET_ADMIN_PERMISSIONS
        }

    @property
    def class_name(self):
        return self.__class__.__name__

    def view_count_up(self, user, do_local=False):
        """ increase view counter, if user is not owner and not super

        @param user which views layer
        @type User model

        @param do_local - do local counter update even if pubsub is enabled
        @type bool
        """
        if user == self.owner or user.is_superuser:
            return
        if not do_local:
            from geonode.messaging import producer
            producer.viewing_dataset(str(user), str(self.owner), self.id)

        else:
            Dataset.objects.filter(id=self.id)\
                .update(popular_count=models.F('popular_count') + 1)


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
    dataset = models.ForeignKey(
        Dataset,
        blank=False,
        null=False,
        unique=False,
        on_delete=models.CASCADE,
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

    """
    Attribute FeatureInfo-Type list
    """
    TYPE_PROPERTY = 'type_property'
    TYPE_HREF = 'type_href'
    TYPE_IMAGE = 'type_image'
    TYPE_VIDEO_MP4 = 'type_video_mp4'
    TYPE_VIDEO_OGG = 'type_video_ogg'
    TYPE_VIDEO_WEBM = 'type_video_webm'
    TYPE_VIDEO_3GP = 'type_video_3gp'
    TYPE_VIDEO_FLV = 'type_video_flv'
    TYPE_VIDEO_YOUTUBE = 'type_video_youtube'
    TYPE_AUDIO = 'type_audio'
    TYPE_IFRAME = 'type_iframe'

    TYPES = ((TYPE_PROPERTY, _("Label"),),
             (TYPE_HREF, _("URL"),),
             (TYPE_IMAGE, _("Image",),),
             (TYPE_VIDEO_MP4, _("Video (mp4)",),),
             (TYPE_VIDEO_OGG, _("Video (ogg)",),),
             (TYPE_VIDEO_WEBM, _("Video (webm)",),),
             (TYPE_VIDEO_3GP, _("Video (3gp)",),),
             (TYPE_VIDEO_FLV, _("Video (flv)",),),
             (TYPE_VIDEO_YOUTUBE, _("Video (YouTube/VIMEO - embedded)",),),
             (TYPE_AUDIO, _("Audio",),),
             (TYPE_IFRAME, _("IFRAME",),),
             )
    featureinfo_type = models.CharField(
        _('featureinfo type'),
        help_text=_('specifies if the attribute should be rendered with an HTML widget on GetFeatureInfo template.'),
        max_length=255,
        unique=False,
        blank=False,
        null=False,
        default=TYPE_PROPERTY,
        choices=TYPES)

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
    last_stats_updated = models.DateTimeField(_('last modified'), default=now, help_text=_(
        'date when attribute statistics were last updated'))  # passing the method itself, not

    objects = AttributeManager()

    def __str__(self):
        return str(
            self.attribute_label if self.attribute_label else self.attribute)

    def unique_values_as_list(self):
        return self.unique_values.split(',')
