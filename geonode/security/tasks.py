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

from celery import shared_task
from django.conf import settings
from .utils import sync_resources_with_guardian


@shared_task
def synch_guardian():
    """
    Sync resources with Guardian and clear their dirty state
    """
    if getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
        sync_resources_with_guardian()
