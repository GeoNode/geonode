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

from logging import getLogger
from celery.task import task
from geonode.geoserver.helpers import gs_slurp
from geonode.documents.models import Document
from geonode.documents.renderers import (
    render_document,
    generate_thumbnail_content,
    ConversionError,
    MissingPILError,
)


logger = getLogger(__name__)


@task(name='geonode.tasks.update.geoserver_update_layers', queue='update')
def geoserver_update_layers(*args, **kwargs):
    """
    Runs update layers.
    """
    return gs_slurp(*args, **kwargs)


@task(name='geonode.tasks.update.create_document_thumbnail', queue='update')
def create_document_thumbnail(object_id):
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

    if not image_path:
        image_path = document.find_placeholder()

    if not image_path:
        logger.debug("Could not find placeholder for document #{}"
                     .format(object_id))
        return

    try:
        thumbnail_content = generate_thumbnail_content(image_path)
    except MissingPILError:
        logger.error('Pillow not installed, could not generate thumbnail.')
        return

    filename = 'document-{}-thumb.png'.format(document.uuid)
    document.save_thumbnail(filename, thumbnail_content)
    logger.debug("Thumbnail for document #{} created.".format(object_id))
