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

from geonode.celery_app import app
from celery.utils.log import get_task_logger

from geonode.documents.models import Document
from geonode.documents.renderers import render_document
from geonode.documents.renderers import generate_thumbnail_content
from geonode.documents.renderers import ConversionError

from django.core.files.storage import default_storage as storage

logger = get_task_logger(__name__)


@app.task(bind=True, queue='update')
def create_document_thumbnail(self, object_id):
    """
    Create thumbnail for a document.
    """
    logger.debug("Generating thumbnail for document #{}.".format(object_id))

    try:
        document = Document.objects.get(id=object_id)
    except Document.DoesNotExist:
        logger.error("Document #{} does not exist.".format(object_id))
        return

    if not storage.exists(document.doc_file.name):
        logger.error("Document #{} exists but its location could not be resolved.".format(object_id))
        return

    image_path = None
    image_file = None

    if document.is_image():
        image_file = storage.open(document.doc_file.name, 'rb')
    elif document.is_file():
        try:
            document_location = storage.path(document.doc_file.name)
        except NotImplementedError as e:
            logger.debug(e)
            document_location = storage.url(document.doc_file.name)

        try:
            image_path = render_document(document_location)
            if image_path is not None:
                try:
                    image_file = open(image_path, 'rb')
                except Exception as e:
                    logger.debug(e)
                    logger.debug("Failed to render document #{}".format(object_id))
            else:
                logger.debug("Failed to render document #{}".format(object_id))
        except ConversionError as e:
            logger.debug("Could not convert document #{}: {}.".format(object_id, e))
        except NotImplementedError as e:
            logger.debug("Failed to render document #{}: {}".format(object_id, e))

    thumbnail_content = None
    try:
        try:
            thumbnail_content = generate_thumbnail_content(image_file)
        except Exception:
            thumbnail_content = generate_thumbnail_content(document.find_placeholder())
    except Exception as e:
        logger.error("Could not generate thumbnail: {}".format(e))
        return
    finally:
        if image_file is not None:
            image_file.close()

        if image_path is not None:
            os.remove(image_path)

    if not thumbnail_content:
        logger.warning("Thumbnail for document #{} empty.".format(object_id))
    filename = 'document-{}-thumb.png'.format(document.uuid)
    document.save_thumbnail(filename, thumbnail_content)
    logger.debug("Thumbnail for document #{} created.".format(object_id))


@app.task(bind=True, queue='cleanup')
def delete_orphaned_document_files(self):
    from geonode.documents.utils import delete_orphaned_document_files
    delete_orphaned_document_files()


@app.task(bind=True, queue='cleanup')
def delete_orphaned_thumbnails(self):
    from geonode.base.utils import delete_orphaned_thumbs
    delete_orphaned_thumbs()
