# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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
import operator
import traceback

from functools import reduce
from django.db.models import Q
from django.contrib.auth.models import Permission
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

from guardian.shortcuts import (
    assign_perm,
    get_perms,
    get_groups_with_perms)

from geonode.groups.models import GroupProfile

from .permissions import (
    VIEW_PERMISSIONS,
    ADMIN_PERMISSIONS,
    LAYER_ADMIN_PERMISSIONS)

from .utils import (
    get_users_with_perms,
    get_user_obj_perms_model)

logger = logging.getLogger(__name__)


class PermissionLevelError(Exception):
    pass


class PermissionLevelMixin(object):

    """
    Mixin for adding "Permission Level" methods
    to a model class -- eg role systems where a
    user has exactly one assigned role with respect to
    an object representing an "access level"
    """

    def get_all_level_info(self):
        resource = self.get_self_resource()
        users = get_users_with_perms(resource)
        groups = get_groups_with_perms(
            resource,
            attach_perms=True)
        if groups:
            for group in groups:
                try:
                    group_profile = GroupProfile.objects.get(slug=group.name)
                    managers = group_profile.get_managers()
                    if managers:
                        for manager in managers:
                            if manager not in users and not manager.is_superuser and \
                                    manager != resource.owner:
                                for perm in ADMIN_PERMISSIONS + VIEW_PERMISSIONS:
                                    assign_perm(perm, manager, resource)
                                users[manager] = ADMIN_PERMISSIONS + VIEW_PERMISSIONS
                except GroupProfile.DoesNotExist:
                    tb = traceback.format_exc()
                    logger.debug(tb)
        if resource.group:
            try:
                group_profile = GroupProfile.objects.get(slug=resource.group.name)
                managers = group_profile.get_managers()
                if managers:
                    for manager in managers:
                        if manager not in users and not manager.is_superuser and \
                                manager != resource.owner:
                            for perm in ADMIN_PERMISSIONS + VIEW_PERMISSIONS:
                                assign_perm(perm, manager, resource)
                            users[manager] = ADMIN_PERMISSIONS + VIEW_PERMISSIONS
            except GroupProfile.DoesNotExist:
                tb = traceback.format_exc()
                logger.debug(tb)
        info = {
            'users': users,
            'groups': groups}

        try:
            if hasattr(self, "layer"):
                info_layer = {
                    'users': get_users_with_perms(
                        self.layer),
                    'groups': get_groups_with_perms(
                        self.layer,
                        attach_perms=True)}
                for user in info_layer['users']:
                    if user in info['users']:
                        info['users'][user] = info['users'][user] + info_layer['users'][user]
                    else:
                        info['users'][user] = info_layer['users'][user]
                for group in info_layer['groups']:
                    if group in info['groups']:
                        info['groups'][group] = list(dict.fromkeys(info['groups'][group] + info_layer['groups'][group]))
                    else:
                        info['groups'][group] = info_layer['groups'][group]
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
        return info

    def get_self_resource(self):
        try:
            if hasattr(self, "resourcebase_ptr_id"):
                return self.resourcebase_ptr
        except ObjectDoesNotExist:
            pass
        return self

    def set_default_permissions(self, owner=None):
        from geonode.resource.manager import resource_manager
        return resource_manager.set_permissions(self.uuid, instance=self, owner=owner, permissions=None)

    def set_permissions(self, perm_spec, created=False):
        from geonode.resource.manager import resource_manager
        return resource_manager.set_permissions(self.uuid, instance=self, permissions=perm_spec, created=created)

    def set_workflow_perms(self, approved=False, published=False):
        from geonode.resource.manager import resource_manager
        return resource_manager.set_workflow_permissions(self.uuid, instance=self, approved=approved, published=published)

    def get_user_perms(self, user):
        """
        Returns a list of permissions a user has on a given resource
        """
        # To avoid circular import
        from geonode.base.models import Configuration

        config = Configuration.load()
        ctype = ContentType.objects.get_for_model(self)
        PERMISSIONS_TO_FETCH = VIEW_PERMISSIONS + ADMIN_PERMISSIONS + LAYER_ADMIN_PERMISSIONS

        resource_perms = Permission.objects.filter(
            codename__in=PERMISSIONS_TO_FETCH,
            content_type_id=ctype.id
        ).values_list('codename', flat=True)

        # Don't filter for admin users
        if not (user.is_superuser or user.is_staff):
            user_model = get_user_obj_perms_model(self)
            user_resource_perms = user_model.objects.filter(
                object_pk=self.pk,
                content_type_id=ctype.id,
                user__username=str(user),
                permission__codename__in=resource_perms
            )
            # get user's implicit perms for anyone flag
            implicit_perms = get_perms(user, self)

            resource_perms = user_resource_perms.union(
                user_model.objects.filter(permission__codename__in=implicit_perms)
            ).values_list('permission__codename', flat=True)

        # filter out permissions for edit, change or publish if readonly mode is active
        perm_prefixes = ['change', 'delete', 'publish']
        if config.read_only:
            clauses = (Q(codename__contains=prefix) for prefix in perm_prefixes)
            query = reduce(operator.or_, clauses)
            if (user.is_superuser or user.is_staff):
                resource_perms = resource_perms.exclude(query)
            else:
                perm_objects = Permission.objects.filter(codename__in=resource_perms)
                resource_perms = perm_objects.exclude(query).values_list('codename', flat=True)

        return resource_perms

    def user_can(self, user, permission):
        """
        Checks if a has a given permission to the resource
        """
        resource = self.get_self_resource()
        user_perms = self.get_user_perms(user).union(resource.get_user_perms(user))

        if permission not in user_perms:
            # TODO cater for permissions with syntax base.permission_codename
            # eg 'base.change_resourcebase'
            return False

        return True
