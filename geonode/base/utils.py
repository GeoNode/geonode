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

"""Utilities for managing GeoNode base models
"""

# Standard Modules
import os

# Django functionality
from django.conf import settings

# Geonode functionality
from geonode.documents.models import ResourceBase


def delete_orphaned_thumbs():
    """
    Deletes orphaned thumbnails.
    """
    documents_path = os.path.join(settings.MEDIA_ROOT, 'thumbs')
    for filename in os.listdir(documents_path):
        fn = os.path.join(documents_path, filename)
        model = filename.split('-')[0]
        uuid = filename.replace(model, '').replace('-thumb.png', '')[1:]
        if ResourceBase.objects.filter(uuid=uuid).count() == 0:
            print 'Removing orphan thumb %s' % fn
            try:
                os.remove(fn)
            except OSError:
                print 'Could not delete file %s' % fn
