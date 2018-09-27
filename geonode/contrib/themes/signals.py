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

from django.dispatch import receiver
from django.db.models import signals
from django.core.management import call_command

from .models import GeoNodeThemeCustomization
from .utils import deactivate_theme

logger = logging.getLogger(__name__)


@receiver(signals.post_delete, sender=GeoNodeThemeCustomization)
def deactivate_theme_signal(sender, **kwargs):
    theme = kwargs["instance"]
    deactivate_theme(theme)
    call_command(
        'collectstatic',
        '--noinput')
