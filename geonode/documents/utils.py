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

# Django functionality
from django.conf import settings

# Geonode functionality
from geonode.documents.models import Document


def delete_orphaned_document_files():
    """
    Deletes orphaned files of deleted documents.
    """
    documents_path = os.path.join(settings.MEDIA_ROOT, 'documents')
    for filename in os.listdir(documents_path):
        fn = os.path.join(documents_path, filename)
        if Document.objects.filter(doc_file__contains=filename).count() == 0:
            print 'Removing orphan document %s' % fn
            try:
                os.remove(fn)
            except OSError:
                print 'Could not delete file %s' % fn
