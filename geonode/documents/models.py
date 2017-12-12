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

import logging
import os
import uuid
from urlparse import urlparse

from django.db import models
from django.db.models import signals
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.contrib.contenttypes import generic
from django.contrib.staticfiles import finders
from django.utils.translation import ugettext_lazy as _

from geonode.layers.models import Layer
from geonode.base.models import ResourceBase, resourcebase_post_save, Link
from geonode.documents.enumerations import DOCUMENT_TYPE_MAP, DOCUMENT_MIMETYPE_MAP
from geonode.maps.signals import map_changed_signal
from geonode.maps.models import Map
from geonode.security.models import remove_object_permissions

from agon_ratings.models import OverallRating
from dialogos.models import Comment
from django.db.models import Avg

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
                                max_length=255,
                                verbose_name=_('File'))

    extension = models.CharField(max_length=128, blank=True, null=True)

    doc_type = models.CharField(max_length=128, blank=True, null=True)

    doc_url = models.URLField(
        blank=True,
        null=True,
        max_length=255,
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
                u'Generating a thumbnail for document: {0}'.format(
                    self.title))
            try:
                with image.Image(filename=self.doc_file.path) as img:
                    img.sample(*size)
                    return img.make_blob('png')
            except:
                logger.debug('Error generating the thumbnail with Wand, cascading to a default image...')
        # if we are still here, we use a default image thumb
        if self.extension and self.extension.lower() in IMGTYPES and self.doc_file:
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

    # elasticsearch_dsl indexing
    def indexing(self):
        if settings.ES_SEARCH:
            from elasticsearch_app.search import DocumentIndex
            obj = DocumentIndex(
                meta={'id': self.id},
                id=self.id,
                abstract=self.abstract,
                category__gn_description=self.prepare_category_gn_description(),
                csw_type=self.csw_type,
                csw_wkt_geometry=self.csw_wkt_geometry,
                detail_url=self.get_absolute_url(),
                owner__username=self.prepare_owner(),
                popular_count=self.popular_count,
                share_count=self.share_count,
                rating=self.prepare_rating(),
                srid=self.srid,
                supplemental_information=self.prepare_supplemental_information(),
                thumbnail_url=self.thumbnail_url,
                uuid=self.uuid,
                title=self.title,
                date=self.date,
                type=self.prepare_type(),
                title_sortable=self.prepare_title_sortable(),
                category=self.prepare_category(),
                bbox_left=self.bbox_x0,
                bbox_right=self.bbox_x1,
                bbox_bottom=self.bbox_y0,
                bbox_top=self.bbox_y1,
                temporal_extent_start=self.temporal_extent_start,
                temporal_extent_end=self.temporal_extent_end,
                keywords=self.keyword_slug_list(),
                regions=self.region_name_list(),
                num_ratings=self.prepare_num_ratings(),
                num_comments=self.prepare_num_comments(),
            )
            obj.save()
            return obj.to_dict(include_meta=True)

    # elasticsearch_dsl indexing helper functions
    def prepare_type(self):
        return "document"

    def prepare_rating(self):
        ct = ContentType.objects.get_for_model(self)
        try:
            rating = OverallRating.objects.filter(
                object_id=self.pk,
                content_type=ct
            ).aggregate(r=Avg("rating"))["r"]
            return float(str(rating or "0"))
        except OverallRating.DoesNotExist:
            return 0.0

    def prepare_title_sortable(self):
        return self.title.lower()

    def prepare_num_ratings(self):
        ct = ContentType.objects.get_for_model(self)
        try:
            return OverallRating.objects.filter(
                object_id=self.pk,
                content_type=ct
            ).all().count()
        except OverallRating.DoesNotExist:
            return 0

    def prepare_num_comments(self):
        ct = ContentType.objects.get_for_model(self)
        try:
            return Comment.objects.filter(
                object_id=self.pk,
                content_type=ct
            ).all().count()
        except:
            return 0

    def prepare_category(self):
        if self.category:
            return self.category.identifier
        else:
            return None

    def prepare_category_gn_description(self):
        if self.category:
            return self.category.gn_description
        else:
            return None

    def prepare_owner(self):
        if self.owner:
            return self.owner.username
        else:
            return None

    def prepare_supplemental_information(self):
        # For some reason this isn't a string
        return str(self.supplemental_information)

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
        doc_type_map = DOCUMENT_TYPE_MAP
        doc_type_map.update(getattr(settings, 'DOCUMENT_TYPE_MAP', {}))
        if doc_type_map is None:
            doc_type = 'other'
        else:
            doc_type = doc_type_map.get(instance.extension, 'other')
        instance.doc_type = doc_type

    elif instance.doc_url:
        if '.' in urlparse(instance.doc_url).path:
            instance.extension = urlparse(instance.doc_url).path.rsplit('.')[-1]

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


def post_save_document(instance, *args, **kwargs):

    name = None
    ext = instance.extension
    mime_type_map = DOCUMENT_MIMETYPE_MAP
    mime_type_map.update(getattr(settings, 'DOCUMENT_MIMETYPE_MAP', {}))
    mime = mime_type_map.get(ext, 'text/plain')
    url = None

    if instance.doc_file:
        name = "Hosted Document"
        url = '%s%s' % (
            settings.SITEURL[:-1],
            reverse('document_download', args=(instance.id,)))
    elif instance.doc_url:
        name = "External Document"
        url = instance.doc_url

    if name and url:
        Link.objects.get_or_create(
            resource=instance.resourcebase_ptr,
            url=url,
            defaults=dict(
                extension=ext,
                name=name,
                mime=mime,
                url=url,
                link_type='data',))


def create_thumbnail(sender, instance, created, **kwargs):
    from geonode.tasks.update import create_document_thumbnail

    create_document_thumbnail.delay(object_id=instance.id)


def update_documents_extent(sender, **kwargs):
    model = 'map' if isinstance(sender, Map) else 'layer'
    ctype = ContentType.objects.get(model=model)
    for document in Document.objects.filter(content_type=ctype, object_id=sender.id):
        document.save()


def pre_delete_document(instance, sender, **kwargs):
    remove_object_permissions(instance.get_self_resource())


signals.pre_save.connect(pre_save_document, sender=Document)
signals.post_save.connect(create_thumbnail, sender=Document)
signals.post_save.connect(post_save_document, sender=Document)
signals.post_save.connect(resourcebase_post_save, sender=Document)
signals.pre_delete.connect(pre_delete_document, sender=Document)
map_changed_signal.connect(update_documents_extent)
