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
import uuid
import logging

from django.db import models
from django.db.models import signals
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.core.files.storage import FileSystemStorage

from pinax.ratings.models import OverallRating
from tinymce.models import HTMLField

from geonode.base.models import ResourceBase, ResourceBaseManager, resourcebase_post_save
from geonode.people.utils import get_valid_user
from geonode.utils import check_shp_columnnames
from geonode.security.utils import ResourceManager
from geonode.security.models import PermissionLevelMixin
from geonode.notifications_helper import (
    send_notification,
    get_notification_recipients)

from ..services.enumerations import CASCADED
from ..services.enumerations import INDEXED

logger = logging.getLogger(__name__)

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

# these are only used if there is no user-configured value in the settings
_DEFAULT_CASCADE_WORKSPACE = "cascaded-services"
_DEFAULT_WORKSPACE = "cascaded-services"


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
            layer = self.layer_styles.first()
            """:type: Layer"""
            return layer.get_self_resource()
        except Exception:
            return None


class LayerManager(ResourceBaseManager):

    def __init__(self):
        models.Manager.__init__(self)


class UploadSession(models.Model):

    """Helper class to keep track of uploads.
    """
    resource = models.ForeignKey(ResourceBase, blank=True, null=True, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    processed = models.BooleanField(default=False)
    error = models.TextField(blank=True, null=True)
    traceback = models.TextField(blank=True, null=True)
    context = models.TextField(blank=True, null=True)

    def successful(self):
        return self.processed and self.errors is None

    def __str__(self):
        _s = f"[Upload session-id: {self.id}]"
        try:
            _s += f" - {self.resource.title}"
        except Exception:
            pass
        return str(_s)

    def __unicode__(self):
        return str(self.__str__())


class Layer(ResourceBase):

    """
    Layer (inherits ResourceBase fields)
    """

    PERMISSIONS = {
        'write': [
            'change_layer_data',
            'change_layer_style',
        ]
    }

    # internal fields
    objects = LayerManager()
    workspace = models.CharField(_('Workspace'), max_length=255)
    store = models.CharField(_('Store'), max_length=255)
    storeType = models.CharField(_('Storetype'), max_length=255)
    name = models.CharField(_('Name'), max_length=255)
    typename = models.CharField(_('Typename'), max_length=255, null=True, blank=True)

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

    default_style = models.ForeignKey(
        Style,
        on_delete=models.SET_NULL,
        related_name='layer_default_style',
        null=True,
        blank=True)

    styles = models.ManyToManyField(Style, related_name='layer_styles')

    remote_service = models.ForeignKey("services.Service", null=True, blank=True, on_delete=models.CASCADE)

    charset = models.CharField(max_length=255, default='UTF-8')

    upload_session = models.ForeignKey(UploadSession, blank=True, null=True, on_delete=models.CASCADE)

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
        return self.storeType == 'dataStore'

    def get_upload_session(self):
        return self.upload_session

    @property
    def processed(self):
        self.upload_session = UploadSession.objects.filter(resource=self).first()
        if self.upload_session:
            if self.upload_session.processed:
                self.clear_dirty_state()
            else:
                self.set_dirty_state()
        else:
            self.clear_dirty_state()
        return not self.dirty_state

    @property
    def display_type(self):
        if self.storeType == "dataStore":
            return "Vector Data"
        elif self.storeType == "coverageStore":
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
    def ows_url(self):
        if self.remote_service is not None and self.remote_service.method == INDEXED:
            result = self.remote_service.service_url
        else:
            result = f"{(settings.OGC_SERVER['default']['PUBLIC_LOCATION'])}ows"
        return result

    @property
    def ptype(self):
        return self.remote_service.ptype if self.remote_service else "gxp_wmscsource"

    @property
    def service_typename(self):
        if self.remote_service is not None:
            return f"{self.remote_service.name}:{self.alternate}"
        else:
            return self.alternate

    @property
    def attributes(self):
        if self.attribute_set and self.attribute_set.count():
            _attrs = self.attribute_set
        else:
            _attrs = Attribute.objects.filter(layer=self)
        return _attrs.exclude(attribute='the_geom').order_by('display_order')

    # layer geometry type.
    @property
    def gtype(self):
        # return attribute type without 'gml:' and 'PropertyType'
        if self.attribute_set and self.attribute_set.count():
            _attrs = self.attribute_set
        else:
            _attrs = Attribute.objects.filter(layer=self)
        if _attrs.filter(attribute='the_geom').exists():
            _att_type = _attrs.filter(attribute='the_geom').first().attribute_type
            _gtype = re.match(r'gml:(.*)PropertyType', _att_type)
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
        if self.storeType == 'dataStore':
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
        return reverse(
            'layer_detail',
            args=(f"{self.store}:{self.alternate}",)
        )

    @property
    def embed_url(self):
        return reverse('layer_embed', kwargs={'layername': self.service_typename})

    def attribute_config(self):
        # Get custom attribute sort order and labels if any
        cfg = {}
        visible_attributes = self.attribute_set.visible()
        if (visible_attributes.exists()):
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
        return MapLayer.objects.filter(name=self.alternate)

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
            producer.viewing_layer(str(user), str(self.owner), self.id)

        else:
            Layer.objects.filter(id=self.id)\
                         .update(popular_count=models.F('popular_count') + 1)


class LayerFile(models.Model):

    """Helper class to store original files.
    """
    upload_session = models.ForeignKey(UploadSession, on_delete=models.CASCADE)
    name = models.CharField(max_length=4096)
    base = models.BooleanField(default=False)
    file = models.FileField(
        upload_to='layers/%Y/%m/%d',
        storage=FileSystemStorage(
            base_url=settings.LOCAL_MEDIA_URL),
        max_length=4096)


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


def _get_alternate_name(instance):
    if instance.remote_service is not None and instance.remote_service.method == INDEXED:
        result = instance.name
    elif instance.remote_service is not None and instance.remote_service.method == CASCADED:
        _ws = getattr(settings, "CASCADE_WORKSPACE", _DEFAULT_CASCADE_WORKSPACE)
        result = f"{_ws}:{instance.name}"
    else:  # we are not dealing with a service-related instance
        _ws = getattr(settings, "DEFAULT_WORKSPACE", _DEFAULT_WORKSPACE)
        result = f"{_ws}:{instance.name}"
    return result


def pre_save_layer(instance, sender, **kwargs):
    if kwargs.get('raw', False):
        try:
            _resourcebase_ptr = instance.resourcebase_ptr
            instance.owner = _resourcebase_ptr.owner
            instance.uuid = _resourcebase_ptr.uuid
            instance.bbox_polygon = _resourcebase_ptr.bbox_polygon
            instance.srid = _resourcebase_ptr.srid
        except Exception as e:
            logger.exception(e)

    if instance.abstract == '' or instance.abstract is None:
        instance.abstract = 'No abstract provided'
    if instance.title == '' or instance.title is None:
        instance.title = instance.name

    # Set a default user for accountstream to work correctly.
    if instance.owner is None:
        instance.owner = get_valid_user()

    logger.debug("handling UUID In pre_save_layer")
    if hasattr(settings, 'LAYER_UUID_HANDLER') and settings.LAYER_UUID_HANDLER != '':
        logger.debug("using custom uuid handler In pre_save_layer")
        from geonode.layers.utils import get_uuid_handler
        instance.uuid = get_uuid_handler()(instance).create_uuid()
    else:
        if instance.uuid == '':
            instance.uuid = str(uuid.uuid4())

    logger.debug("In pre_save_layer")
    if instance.alternate is None:
        instance.alternate = _get_alternate_name(instance)
    logger.debug(f"instance.alternate is: {instance.alternate}")

    base_file, info = instance.get_base_file()

    if info:
        instance.info = info

    if base_file is not None:
        extension = f'.{base_file.name}'
        if extension in vec_exts:
            instance.storeType = 'dataStore'
        elif extension in cov_exts:
            instance.storeType = 'coverageStore'

    if instance.bbox_polygon is None:
        instance.set_bbox_polygon((-180, -90, 180, 90), 'EPSG:4326')

    # Send a notification when a layer is created
    if instance.pk is None and instance.title:
        # Resource Created
        notice_type_label = f'{instance.class_name.lower()}_created'
        recipients = get_notification_recipients(notice_type_label, resource=instance)
        send_notification(recipients, notice_type_label, {'resource': instance})


def pre_delete_layer(instance, sender, **kwargs):
    """
    Remove any associated style to the layer, if it is not used by other layers.
    Default style will be deleted in post_delete_layer
    """
    if instance.remote_service is not None and instance.remote_service.method == INDEXED:
        # we need to delete the maplayers here because in the post save layer.remote_service is not available anymore
        # REFACTOR
        from geonode.maps.models import MapLayer
        logger.debug(
            "Going to delete associated maplayers for [%s]",
            instance.alternate)
        MapLayer.objects.filter(
            name=instance.alternate,
            ows_url=instance.ows_url).delete()

    logger.debug(
        "Going to delete the styles associated for [%s]",
        instance.alternate)
    ct = ContentType.objects.get_for_model(instance)
    OverallRating.objects.filter(
        content_type=ct,
        object_id=instance.id).delete()

    default_style = instance.default_style
    for style in instance.styles.all():
        if style.layer_styles.all().count() == 1:
            if style != default_style:
                style.delete()

    if 'geonode.upload' in settings.INSTALLED_APPS and \
            settings.UPLOADER['BACKEND'] == 'geonode.importer':
        from geonode.upload.models import Upload
        # Need to call delete one by one in ordee to invoke the
        #  'delete' overridden method
        for upload in Upload.objects.filter(layer_id=instance.id):
            upload.delete()

    # Delete object permissions
    ResourceManager.remove_permissions(instance.uuid, instance=instance.get_self_resource())


def post_delete_layer(instance, sender, **kwargs):
    """
    - Remove any associated style to the layer, if it is not used by other layers.
    - Default style will be deleted in post_delete_dataset.
    - Remove the layer from any associated map, if any.
    - Remove the layer default style.
    """
    try:
        if instance.get_real_instance().remote_service is not None:
            from geonode.services.models import HarvestJob
            _resource_id = instance.get_real_instance().alternate
            HarvestJob.objects.filter(
                service=instance.get_real_instance().remote_service, resource_id=_resource_id).delete()
            _resource_id = instance.get_real_instance().alternate.split(":")[-1] if len(instance.get_real_instance().alternate.split(":")) else None
            if _resource_id:
                HarvestJob.objects.filter(
                    service=instance.get_real_instance().remote_service, resource_id=_resource_id).delete()
    except Exception as e:
        logger.exception(e)

    from geonode.maps.models import MapLayer
    logger.debug(
        "Going to delete associated maplayers for [%s]", instance.name)
    MapLayer.objects.filter(
        name=instance.alternate,
        ows_url=instance.ows_url).delete()

    logger.debug(
        "Going to delete the default style for [%s]", instance.name)

    if instance.default_style and Layer.objects.filter(
            default_style__id=instance.default_style.id).count() == 0:
        instance.default_style.delete()

    try:
        if instance.upload_session:
            for lf in instance.upload_session.layerfile_set.all():
                lf.file.delete()
            instance.upload_session.delete()
    except UploadSession.DoesNotExist:
        pass


def post_delete_layer_file(instance, sender, **kwargs):
    """Delete associated file.

    :param instance: LayerFile instance
    :type instance: LayerFile
    """
    instance.file.delete(save=False)


signals.pre_save.connect(pre_save_layer, sender=Layer)
signals.post_save.connect(resourcebase_post_save, sender=Layer)
signals.pre_delete.connect(pre_delete_layer, sender=Layer)
signals.post_delete.connect(post_delete_layer, sender=Layer)
signals.post_delete.connect(post_delete_layer_file, sender=LayerFile)
