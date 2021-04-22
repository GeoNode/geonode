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
import logging

logger = logging.getLogger(__name__)

default_app_config = 'geonode.groups.apps.GroupsAppConfig'


def init_registered_members_groupprofile():
    from .conf import settings
    from .models import GroupProfile
    from django.contrib.auth import get_user_model

    group_name = settings.REGISTERED_MEMBERS_GROUP_NAME
    group_title = settings.REGISTERED_MEMBERS_GROUP_TITLE
    logger.debug(f"Creating {group_name} default Group Profile")
    groupprofile, created = GroupProfile.objects.get_or_create(
        slug=group_name)
    if created:
        groupprofile.slug = group_name
        groupprofile.title = group_title
        groupprofile.access = "private"
        groupprofile.save()

    User = get_user_model()
    for _u in User.objects.filter(is_active=True):
        if not _u.is_anonymous and _u != User.get_anonymous() and \
                not groupprofile.user_is_member(_u):
            groupprofile.join(_u)
