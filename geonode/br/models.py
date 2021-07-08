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
from datetime import datetime

from django.db import models

logger = logging.getLogger(__name__)


class RestoredBackup(models.Model):
    name = models.CharField(blank=True, max_length=400)
    archive_md5 = models.CharField(blank=False, null=False, max_length=32)
    restoration_date = models.DateTimeField(blank=False, null=False, default=datetime.now)
    creation_date = models.DateTimeField()
