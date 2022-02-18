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

from urllib.parse import urljoin

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.contrib.staticfiles import finders
from django.utils.functional import classproperty
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from geonode.client.hooks import hookset
from geonode.maps.models import Map
from geonode.layers.models import Dataset
from geonode.base.models import ResourceBase
from geonode.maps.signals import map_changed_signal
from geonode.groups.conf import settings as groups_settings
from geonode.documents.enumerations import (
    DOCUMENT_TYPE_MAP,
    DOCUMENT_MIMETYPE_MAP)
from geonode.security.permissions import (
    VIEW_PERMISSIONS,
    OWNER_PERMISSIONS,
    DOWNLOAD_PERMISSIONS)
from geonode.utils import build_absolute_uri

logger = logging.getLogger(__name__)


class Document(ResourceBase):

    """
    A document is any kind of information that can be attached to a map such as pdf, images, videos, xls...
    """

    extension = models.CharField(max_length=128, blank=True, null=True)

    doc_url = models.URLField(
        blank=True,
        null=True,
        max_length=255,
        help_text=_('The URL of the document if it is external.'),
        verbose_name=_('URL'))

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return hookset.document_detail_url(self)

    @classproperty
    def allowed_permissions(cls):
        return {
            "anonymous": VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS,
            "default": OWNER_PERMISSIONS + DOWNLOAD_PERMISSIONS,
            groups_settings.REGISTERED_MEMBERS_GROUP_NAME: OWNER_PERMISSIONS + DOWNLOAD_PERMISSIONS
        }

    @classproperty
    def compact_permission_labels(cls):
        return {
            "none": _("None"),
            "view": _("View Metadata"),
            "download": _("View and Download"),
            "edit": _("Edit"),
            "manage": _("Manage"),
            "owner": _("Owner")
        }

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
        elif self.files:
            return urljoin(
                settings.SITEURL,
                reverse('document_link', args=(self.id,))
            )

    @property
    def is_file(self):
        return self.files and self.extension

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

    @property
    def embed_url(self):
        return reverse('document_embed', args=(self.id,))

    @property
    def download_url(self):
        return build_absolute_uri(reverse('document_download', args=(self.id,)))

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
    if isinstance(resource, Dataset) or isinstance(resource, Map):
        content_type = ContentType.objects.get_for_model(resource)
        return Document.objects.filter(links__content_type=content_type,
                                       links__object_id=resource.pk)
    else:
        return None


def update_documents_extent(sender, **kwargs):
    documents = get_related_documents(sender)
    if documents:
        for document in documents:
            document.save()


map_changed_signal.connect(update_documents_extent)
