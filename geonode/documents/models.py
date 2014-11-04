import logging
import os
import uuid

from django.db import models
from django.db.models import signals
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.contrib.contenttypes import generic
from django.contrib.staticfiles import finders
from django.utils.translation import ugettext_lazy as _

from geonode.layers.models import Layer
from geonode.base.models import ResourceBase, Thumbnail, Link, resourcebase_post_save
from geonode.maps.signals import map_changed_signal
from geonode.maps.models import Map

IMGTYPES = ['jpg', 'jpeg', 'tif', 'tiff', 'png', 'gif']

logger = logging.getLogger(__name__)


class Document(ResourceBase):

    """
    A document is any kind of information that can be attached to a map such as pdf, images, videos, xls...
    """

    # Relation to the resource model
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    resource = generic.GenericForeignKey('content_type', 'object_id')

    doc_file = models.FileField(upload_to='documents',
                                null=True,
                                blank=True,
                                verbose_name=_('File'))

    extension = models.CharField(max_length=128, blank=True, null=True)

    doc_type = models.CharField(max_length=128, blank=True, null=True)

    doc_url = models.URLField(
        blank=True,
        null=True,
        help_text=_('The URL of the document if it is external.'),
        verbose_name=_('URL'))

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('document_detail', args=(self.id,))

    @property
    def name_long(self):
        if not self.title:
            return str(self.id)
        else:
            return '%s (%s)' % (self.title, self.id)

    def _render_thumbnail(self):
        from cStringIO import StringIO

        size = 200, 150

        try:
            from PIL import Image, ImageOps
        except ImportError, e:
            logger.error(
                '%s: Pillow not installed, cannot generate thumbnails.' %
                e)
            return None

        try:
            # if wand is installed, than use it for pdf thumbnailing
            from wand import image
        except:
            wand_available = False
        else:
            wand_available = True

        if wand_available and self.extension and self.extension.lower(
        ) == 'pdf' and self.doc_file:
            logger.debug(
                'Generating a thumbnail for document: {0}'.format(
                    self.title))
            with image.Image(filename=self.doc_file.path) as img:
                img.sample(*size)
                return img.make_blob('png')
        elif self.extension and self.extension.lower() in IMGTYPES and self.doc_file:

            img = Image.open(self.doc_file.path)
            img = ImageOps.fit(img, size, Image.ANTIALIAS)
        else:
            filename = finders.find('documents/{0}-placeholder.png'.format(self.extension), False) or \
                finders.find('documents/generic-placeholder.png', False)

            if not filename:
                return None

            img = Image.open(filename)

        imgfile = StringIO()
        img.save(imgfile, format='PNG')
        return imgfile.getvalue()

    @property
    def class_name(self):
        return self.__class__.__name__

    class Meta(ResourceBase.Meta):
        pass


def get_related_documents(resource):
    if isinstance(resource, Layer) or isinstance(resource, Map):
        ct = ContentType.objects.get_for_model(resource)
        return Document.objects.filter(content_type=ct, object_id=resource.pk)
    else:
        return None


def pre_save_document(instance, sender, **kwargs):
    base_name, extension, doc_type = None, None, None

    if instance.doc_file:
        base_name, extension = os.path.splitext(instance.doc_file.name)
        instance.extension = extension[1:]
        doc_type_map = settings.DOCUMENT_TYPE_MAP
        if doc_type_map is None:
            doc_type = 'other'
        else:
            if instance.extension in doc_type_map:
                doc_type = doc_type_map[''+instance.extension]
            else:
                doc_type = 'other'
        instance.doc_type = doc_type

    elif instance.doc_url:
        if len(instance.doc_url) > 4 and instance.doc_url[-4] == '.':
            instance.extension = instance.doc_url[-3:]

    if not instance.uuid:
        instance.uuid = str(uuid.uuid1())
    instance.csw_type = 'document'

    if instance.abstract == '' or instance.abstract is None:
        instance.abstract = 'No abstract provided'

    if instance.title == '' or instance.title is None:
        instance.title = instance.doc_file.name

    if instance.resource:
        instance.csw_wkt_geometry = instance.resource.geographic_bounding_box.split(
            ';')[-1]
        instance.bbox_x0 = instance.resource.bbox_x0
        instance.bbox_x1 = instance.resource.bbox_x1
        instance.bbox_y0 = instance.resource.bbox_y0
        instance.bbox_y1 = instance.resource.bbox_y1
    else:
        instance.bbox_x0 = -180
        instance.bbox_x1 = 180
        instance.bbox_y0 = -90
        instance.bbox_y1 = 90


def create_thumbnail(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.has_thumbnail():
        instance.thumbnail_set.get().thumb_file.delete()
    else:
        instance.thumbnail_set.add(Thumbnail())

    image = instance._render_thumbnail()

    instance.thumbnail_set.get().thumb_file.save(
        'doc-%s-thumb.png' %
        instance.id,
        ContentFile(image))
    instance.thumbnail_set.get().thumb_spec = 'Rendered'
    instance.thumbnail_set.get().save()
    Link.objects.get_or_create(
        resource=instance.get_self_resource(),
        url=instance.thumbnail_set.get().thumb_file.url,
        defaults=dict(
            name=('Thumbnail'),
            extension='png',
            mime='image/png',
            link_type='image',))


def update_documents_extent(sender, **kwargs):
    model = 'map' if isinstance(sender, Map) else 'layer'
    ctype = ContentType.objects.get(model=model)
    for document in Document.objects.filter(content_type=ctype, object_id=sender.id):
        document.save()


signals.pre_save.connect(pre_save_document, sender=Document)
signals.post_save.connect(create_thumbnail, sender=Document)
signals.post_save.connect(resourcebase_post_save, sender=Document)
map_changed_signal.connect(update_documents_extent)
