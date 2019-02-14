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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from geonode.layers.models import Layer
from geonode.geoserver.tasks import thumbnail_task

from .utils import (purge_geofence_layer_rules,
                    sync_geofence_with_guardian)  # set_geofence_invalidate_cache

logger = logging.getLogger(__name__)


def _log(msg, *args):
    logger.debug(msg, *args)


@shared_task
def synch_guardian():
    if getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
        from geonode.base.models import ResourceBase
        dirty_resources = ResourceBase.objects.filter(dirty_state=True)
        if dirty_resources and dirty_resources.count() > 0:
            _log(" --------------------------- synching with guardian!")
            for r in dirty_resources:
                if r.polymorphic_ctype.name == 'layer':
                    layer = None
                    try:
                        purge_geofence_layer_rules(r)
                        layer = Layer.objects.get(id=r.id)
                        perm_spec = layer.get_all_level_info()
                        _log(" %s --------------------------- %s " % (layer, perm_spec))

                        # All the other users
                        if 'users' in perm_spec:
                            for user, perms in perm_spec['users'].items():
                                user = get_user_model().objects.get(username=user)
                                # Set the GeoFence User Rules
                                geofence_user = str(user)
                                if "AnonymousUser" in geofence_user:
                                    geofence_user = None
                                sync_geofence_with_guardian(layer, perms, user=geofence_user)

                        # All the other groups
                        if 'groups' in perm_spec:
                            for group, perms in perm_spec['groups'].items():
                                group = Group.objects.get(name=group)
                                # Set the GeoFence Group Rules
                                sync_geofence_with_guardian(layer, perms, group=group)

                        try:
                            thumbnail_task.delay(
                                layer.id,
                                layer.__class__.__name__,
                                overwrite=True,
                                check_bbox=True)
                        except BaseException:
                            logger.warn("!WARNING! - Failure while Creating Thumbnail \
                                for Layer [%s]" % (layer.alternate))

                        r.clear_dirty_state()
                    except BaseException:
                        logger.warn("!WARNING! - Failure Synching-up Security Rules for Resource [%s]" % (r))

            # if set_geofence_invalidate_cache():
            #     for r in dirty_resources:
            #         _log(" --------------------------- clearing %s" % r)
