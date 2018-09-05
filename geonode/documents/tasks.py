# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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
from os import access, R_OK
from os.path import isfile

from celery.app import shared_task
from celery.utils.log import get_task_logger

from geonode.documents.models import Document
from geonode.documents.renderers import render_document
from geonode.documents.renderers import generate_thumbnail_content
from geonode.documents.renderers import ConversionError
from geonode.documents.renderers import MissingPILError

logger = get_task_logger(__name__)


@shared_task(bind=True, queue='update')
def create_document_thumbnail(self, object_id):
    """
    Create thumbnail for a document.
    """
    logger.debug("Generating thumbnail for document #{}.".format(object_id))

    try:
        document = Document.objects.get(id=object_id)
    except Document.DoesNotExist:
        logger.error("Document #{} does not exit.".format(object_id))
        return

    image_path = None

    if document.is_image():
        image_path = document.doc_file.path
    elif document.is_file():
        try:
            image_file = render_document(document.doc_file.path)
            image_path = image_file.name
        except ConversionError as e:
            logger.debug("Could not convert document #{}: {}."
                         .format(object_id, e))

    try:
        if image_path:
            assert isfile(image_path) and access(image_path, R_OK) and os.stat(image_path).st_size > 0
    except (AssertionError, TypeError):
        image_path = None

    if not image_path:
        image_path = document.find_placeholder()

    if not image_path or not os.path.exists(image_path):
        logger.debug("Could not find placeholder for document #{}"
                     .format(object_id))
        return

    thumbnail_content = None
    try:
        thumbnail_content = generate_thumbnail_content(image_path)
    except MissingPILError:
        logger.error('Pillow not installed, could not generate thumbnail.')
        return

    if not thumbnail_content:
        logger.warning("Thumbnail for document #{} empty.".format(object_id))
    filename = 'document-{}-thumb.png'.format(document.uuid)
    document.save_thumbnail(filename, thumbnail_content)
    logger.debug("Thumbnail for document #{} created.".format(object_id))


@shared_task(bind=True, queue='cleanup')
def delete_orphaned_document_files(self):
    from geonode.documents.utils import delete_orphaned_document_files
    delete_orphaned_document_files()


@shared_task(bind=True, queue='cleanup')
def delete_orphaned_thumbnails(self):
    from geonode.documents.utils import delete_orphaned_thumbs
    delete_orphaned_thumbs()
