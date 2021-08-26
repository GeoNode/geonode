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

"""Utilities for managing GeoNode documents
"""

# Standard Modules
import os
import logging

# Django functionality
from django.core.files.storage import default_storage as storage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import loader
from django.utils.translation import ugettext as _
from django.utils.text import slugify
from django_downloadview.response import DownloadResponse

# Geonode functionality
from geonode.documents.models import Document
from geonode.base import register_event
from geonode.monitoring.models import EventType

logger = logging.getLogger(__name__)


def delete_orphaned_document_files():
    """
    Deletes orphaned files of deleted documents.
    """
    deleted = []
    _, files = storage.listdir(os.path.join("documents", "document"))

    for filename in files:
        if Document.objects.filter(doc_file__contains=filename).count() == 0:
            logger.debug(f"Deleting orphaned document {filename}")
            try:
                storage.delete(os.path.join(
                    os.path.join("documents", "document"), filename))
                deleted.append(filename)
            except NotImplementedError as e:
                logger.error(
                    f"Failed to delete orphaned document '{filename}': {e}")

    return deleted


def get_download_response(request, docid, attachment=False):
    """
    Returns a download response if user has access to download the document of a given id,
    and an http response if they have no permissions to download it.
    """
    document = get_object_or_404(Document, pk=docid)

    if not request.user.has_perm(
            'base.download_resourcebase',
            obj=document.get_self_resource()):
        return HttpResponse(
            loader.render_to_string(
                '401.html', context={
                    'error_message': _("You are not allowed to view this document.")}, request=request), status=401)
    if attachment:
        register_event(request, EventType.EVENT_DOWNLOAD, document)
    filename = slugify(os.path.splitext(os.path.basename(document.title))[0])
    return DownloadResponse(
        document.doc_file,
        basename=f'{filename}.{document.extension}',
        attachment=attachment
    )
