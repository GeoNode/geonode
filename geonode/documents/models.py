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

import os
import uuid
import logging
from urllib.parse import urlparse, urljoin

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.db.models import signals
from django.contrib.staticfiles import finders
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from uuid_upload_path import upload_to

from geonode.layers.models import Layer
from geonode.base.models import ResourceBase, resourcebase_post_save, Link
from geonode.documents.enumerations import DOCUMENT_TYPE_MAP, DOCUMENT_MIMETYPE_MAP
from geonode.maps.signals import map_changed_signal
from geonode.maps.models import Map
from geonode.security.utils import remove_object_permissions

logger = logging.getLogger(__name__)


class Document(ResourceBase):

    """
    A document is any kind of information that can be attached to a map such as pdf, images, videos, xls...
    """

    doc_file = models.FileField(
        upload_to=upload_to,
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

    def __str__(self):
        return f"{self.title}"

    def get_absolute_url(self):
        return reverse('document_detail', args=(self.id,))

    @property
    def name(self):
        if not self.title:
            return str(self.id)
        else:
            return self.title

    @property
    def name_long(self):
        if not self.title:
            return str(self.id)
        else:
            return f'{self.title} ({self.id})'

    def find_placeholder(self):
        placeholder = 'documents/{0}-placeholder.png'
        if finders.find(placeholder.format(self.extension), False):
            return finders.find(placeholder.format(self.extension), False)
        elif self.is_audio:
            return finders.find(placeholder.format('audio'), False)
        elif self.is_image:
            return finders.find(placeholder.format('image'), False)
        elif self.is_video:
            return finders.find(placeholder.format('video'), False)
        return finders.find(placeholder.format('generic'), False)

    @property
    def href(self):
        if self.doc_url:
            return self.doc_url
        elif self.doc_file:
            return urljoin(
                settings.SITEURL,
                reverse('document_download', args=(self.id,))
            )

    @property
    def is_file(self):
        return self.doc_file and self.extension

    @property
    def mime_type(self):
        if self.is_file and self.extension.lower() in DOCUMENT_MIMETYPE_MAP:
            return DOCUMENT_MIMETYPE_MAP[self.extension.lower()]
        return None

    @property
    def is_audio(self):
        AUDIOTYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == 'audio']
        return self.is_file and self.extension.lower() in AUDIOTYPES

    @property
    def is_image(self):
        IMGTYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == 'image']
        return self.is_file and self.extension.lower() in IMGTYPES

    @property
    def is_video(self):
        VIDEOTYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == 'video']
        return self.is_file and self.extension.lower() in VIDEOTYPES

    @property
    def class_name(self):
        return self.__class__.__name__

    class Meta(ResourceBase.Meta):
        pass


class DocumentResourceLink(models.Model):

    # relation to the document model
    document = models.ForeignKey(
        Document,
        null=True,
        blank=True,
        related_name='links',
        on_delete=models.CASCADE)

    # relation to the resource model
    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    resource = GenericForeignKey('content_type', 'object_id')


def get_related_documents(resource):
    if isinstance(resource, Layer) or isinstance(resource, Map):
        content_type = ContentType.objects.get_for_model(resource)
        return Document.objects.filter(links__content_type=content_type,
                                       links__object_id=resource.pk)
    else:
        return None


def get_related_resources(document):
    if document.links:
        try:
            return [
                link.content_type.get_object_for_this_type(id=link.object_id)
                for link in document.links.all()
            ]
        except Exception:
            return []
    else:
        return []


def pre_save_document(instance, sender, **kwargs):
    if instance.doc_file:
        base_name, extension = os.path.splitext(instance.doc_file.name)
        instance.extension = extension[1:]
        doc_type_map = DOCUMENT_TYPE_MAP
        doc_type_map.update(getattr(settings, 'DOCUMENT_TYPE_MAP', {}))
        if doc_type_map is None:
            doc_type = 'other'
        else:
            doc_type = doc_type_map.get(
                instance.extension.lower(), 'other')
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

    resources = get_related_resources(instance)

    if resources:
        instance.bbox_x0 = min([r.bbox_x0 for r in resources])
        instance.bbox_x1 = max([r.bbox_x1 for r in resources])
        instance.bbox_y0 = min([r.bbox_y0 for r in resources])
        instance.bbox_y1 = max([r.bbox_y1 for r in resources])
    else:
        instance.bbox_x0 = -180
        instance.bbox_x1 = 180
        instance.bbox_y0 = -90
        instance.bbox_y1 = 90


def post_save_document(instance, *args, **kwargs):
    from .tasks import create_document_thumbnail

    name = None
    ext = instance.extension
    mime_type_map = DOCUMENT_MIMETYPE_MAP
    mime_type_map.update(getattr(settings, 'DOCUMENT_MIMETYPE_MAP', {}))
    mime = mime_type_map.get(ext, 'text/plain')
    url = None

    if instance.id and instance.doc_file:
        name = "Hosted Document"
        site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
        url = '%s%s' % (
            site_url,
            reverse('document_download', args=(instance.id,)))
        create_document_thumbnail.apply_async((instance.id,))
    elif instance.doc_url:
        name = "External Document"
        url = instance.doc_url

    if name and url and ext:
        Link.objects.get_or_create(
            resource=instance.resourcebase_ptr,
            url=url,
            defaults=dict(
                extension=ext,
                name=name,
                mime=mime,
                url=url,
                link_type='data',))


def update_documents_extent(sender, **kwargs):
    documents = get_related_documents(sender)
    if documents:
        for document in documents:
            document.save()


def pre_delete_document(instance, sender, **kwargs):
    remove_object_permissions(instance.get_self_resource())


signals.pre_save.connect(pre_save_document, sender=Document)
signals.post_save.connect(post_save_document, sender=Document)
signals.post_save.connect(resourcebase_post_save, sender=Document)
signals.pre_delete.connect(pre_delete_document, sender=Document)
map_changed_signal.connect(update_documents_extent)
