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

"""Utilities for managing GeoNode documents
"""

# Standard Modules
import os
import logging

# Django functionality
from django.core.files.storage import default_storage as storage

# Geonode functionality
from geonode.documents.models import Document

logger = logging.getLogger(__name__)


def delete_orphaned_document_files():
    """
    Deletes orphaned files of deleted documents.
    """
    deleted = []
    _, files = storage.listdir(os.path.join("documents", "document"))

    for filename in files:
        if Document.objects.filter(doc_file__contains=filename).count() == 0:
            logger.debug("Deleting orphaned document " + filename)
            try:
                storage.delete(os.path.join(
                    os.path.join("documents", "document"), filename))
                deleted.append(filename)
            except NotImplementedError as e:
                logger.error(
                    "Failed to delete orphaned document '{}': {}".format(filename, e))

    return deleted
