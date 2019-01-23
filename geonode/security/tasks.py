# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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
from celery import shared_task

from .utils import set_geofence_invalidate_cache

logger = logging.getLogger(__name__)


def _log(msg, *args):
    logger.info(msg, *args)


@shared_task
def synch_guardian():
    from geonode.base.models import ResourceBase
    dirty_resources = ResourceBase.objects.filter(dirty_state=True)
    if dirty_resources and dirty_resources.count() > 0:
        _log(" --------------------------- synching with guardian!")
        if set_geofence_invalidate_cache():
            for r in dirty_resources:
                _log(" --------------------------- clearing %s" % r)
                r.clear_dirty_state()
