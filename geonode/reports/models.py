#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

from django.db import models
from django.utils.translation import ugettext_lazy as _
from geonode.people.models import Profile
from datetime import datetime

class DownloadCount(models.Model):
    date = models.DateTimeField( default=datetime.now)
    category = models.CharField(_('Category'), max_length=100)
    chart_group = models.CharField(_('Chart Group'), max_length=100)
    download_type = models.CharField(_('Type'), max_length=100)
    count = models.IntegerField(_('Count'))

class SUCLuzViMin(models.Model):
    province =  models.CharField(_('Province'), max_length=100)
    suc = models.CharField(_('Suc'), max_length=100)
    luzvimin = models.CharField(_('LuzViMin'), max_length=100)

class DownloadTracker(models.Model):
    timestamp = models.DateTimeField(default=datetime.now)
    actor = models.ForeignKey(
        Profile
    )
    title = models.CharField(_('Title'), max_length=100)
    resource_type = models.CharField(_('Resource Type'), max_length=100)
    keywords = models.CharField(_('Keywords'), max_length=255)
    dl_type = models.CharField(_('Download Type'), max_length=100)
