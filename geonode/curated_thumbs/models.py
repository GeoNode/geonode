# -*- coding: utf-8 -*-
# ##############################################################################
#
# Copyright (C) 2019 OSGeo
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
# ##############################################################################

from __future__ import unicode_literals

from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from geonode.base.models import ResourceBase


class CuratedThumbnail(models.Model):
    resource = models.OneToOneField(ResourceBase)
    img = models.ImageField(upload_to='curated_thumbs')
    # TOD read thumb size from settings
    img_thumbnail = ImageSpecField(source='img',
                                   processors=[ResizeToFill(240, 180)],
                                   format='PNG',
                                   options={'quality': 60})
