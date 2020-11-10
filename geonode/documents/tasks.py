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

from django.core.files.storage import default_storage as storage

from geonode.celery_app import app
from celery.utils.log import get_task_logger

from geonode.documents.models import Document
from geonode.documents.renderers import render_document
from geonode.documents.renderers import generate_thumbnail_content
from geonode.documents.renderers import ConversionError

logger = get_task_logger(__name__)


@app.task(
    bind=True,
    name='geonode.documents.tasks.create_document_thumbnail',
    queue='update',
    countdown=60,
    # expires=120,
    acks_late=True,
    retry=True,
    retry_policy={
        'max_retries': 10,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    })
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

    image_path = None
    image_file = None

    if document.is_image:
        if not os.path.exists(storage.path(document.doc_file.name)):
            from shutil import copyfile
            copyfile(
                document.doc_file.path,
                storage.path(document.doc_file.name)
            )
        image_file = storage.open(document.doc_file.name, 'rb')
    elif document.is_video or document.is_audio:
        image_file = open(document.find_placeholder(), 'rb')
    elif document.is_file:
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
        except Exception as e:
            logger.error("Could not generate thumbnail, falling back to 'placeholder': {}".format(e))
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


@app.task(
    bind=True,
    name='geonode.documents.tasks.delete_orphaned_document_files',
    queue='cleanup',
    countdown=60,
    # expires=120,
    acks_late=True,
    retry=True,
    retry_policy={
        'max_retries': 10,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    })
def delete_orphaned_document_files(self):
    from geonode.documents.utils import delete_orphaned_document_files
    delete_orphaned_document_files()


@app.task(
    bind=True,
    name='geonode.documents.tasks.delete_orphaned_thumbnails',
    queue='cleanup',
    countdown=60,
    # expires=120,
    acks_late=True,
    retry=True,
    retry_policy={
        'max_retries': 10,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    })
def delete_orphaned_thumbnails(self):
    from geonode.base.utils import delete_orphaned_thumbs
    delete_orphaned_thumbs()
