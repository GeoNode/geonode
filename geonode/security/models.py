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
import traceback

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from geonode.groups.conf import settings as groups_settings

from guardian.shortcuts import (
    assign_perm,
    get_groups_with_perms
)

from geonode.groups.models import GroupProfile

from .utils import (
    get_users_with_perms,
    set_owner_permissions,
    remove_object_permissions,
    purge_geofence_layer_rules,
    sync_geofence_with_guardian
)

logger = logging.getLogger("geonode.security.models")

VIEW_PERMISSIONS = [
    'view_resourcebase',
    'download_resourcebase',
]

ADMIN_PERMISSIONS = [
    'change_resourcebase_metadata',
    'change_resourcebase',
    'delete_resourcebase',
    'change_resourcebase_permissions',
    'publish_resourcebase',
]

LAYER_ADMIN_PERMISSIONS = [
    'change_layer_data',
    'change_layer_style'
]


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
        groups = get_groups_with_perms(resource,
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
                    pass
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
                pass
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

    def set_default_permissions(self):
        """
        Remove all the permissions except for the owner and assign the
        view permission to the anonymous group
        """
        remove_object_permissions(self)

        # default permissions for anonymous users

        def skip_registered_members_common_group(user_group):
            if groups_settings.AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME:
                _members_group_name = groups_settings.REGISTERED_MEMBERS_GROUP_NAME
                if (settings.RESOURCE_PUBLISHING or settings.ADMIN_MODERATE_UPLOADS) and \
                _members_group_name == user_group.name:
                    return True
            return False

        anonymous_group, created = Group.objects.get_or_create(name='anonymous')
        user_groups = Group.objects.filter(
            name__in=self.owner.groupmember_set.all().values_list("group__slug", flat=True))
        obj_group_managers = []
        if user_groups:
            for _user_group in user_groups:
                if not skip_registered_members_common_group(_user_group):
                    try:
                        _group_profile = GroupProfile.objects.get(slug=_user_group.name)
                        managers = _group_profile.get_managers()
                        if managers:
                            for manager in managers:
                                if manager not in obj_group_managers and not manager.is_superuser:
                                    obj_group_managers.append(manager)
                    except GroupProfile.DoesNotExist:
                        pass

        if not anonymous_group:
            raise Exception("Could not acquire 'anonymous' Group.")

        # default permissions for resource owner
        set_owner_permissions(self, members=obj_group_managers)

        # Anonymous
        anonymous_can_view = settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION
        if anonymous_can_view:
            assign_perm('view_resourcebase',
                        anonymous_group, self.get_self_resource())
        else:
            for user_group in user_groups:
                if not skip_registered_members_common_group(user_group):
                    assign_perm('view_resourcebase',
                                user_group, self.get_self_resource())

        anonymous_can_download = settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION
        if anonymous_can_download:
            assign_perm('download_resourcebase',
                        anonymous_group, self.get_self_resource())
        else:
            for user_group in user_groups:
                if not skip_registered_members_common_group(user_group):
                    assign_perm('download_resourcebase',
                                user_group, self.get_self_resource())

        if self.__class__.__name__ == 'Layer':
            # only for layer owner
            assign_perm('change_layer_data', self.owner, self)
            assign_perm('change_layer_style', self.owner, self)
            if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                purge_geofence_layer_rules(self.get_self_resource())

                # Owner & Managers
                perms = [
                    "view_resourcebase",
                    "change_layer_data",
                    "change_layer_style",
                    "change_resourcebase",
                    "change_resourcebase_permissions",
                    "download_resourcebase"]
                sync_geofence_with_guardian(self.layer, perms, user=self.owner)
                for _group_manager in obj_group_managers:
                    sync_geofence_with_guardian(self.layer, perms, user=_group_manager)
                for user_group in user_groups:
                    if not skip_registered_members_common_group(user_group):
                        sync_geofence_with_guardian(self.layer, perms, group=user_group)

                # Anonymous
                perms = ["view_resourcebase"]
                if anonymous_can_view:
                    sync_geofence_with_guardian(self.layer, perms, user=None, group=None)

                perms = ["download_resourcebase"]
                if anonymous_can_download:
                    sync_geofence_with_guardian(self.layer, perms, user=None, group=None)

    def set_permissions(self, perm_spec, created=False):
        """
        Sets an object's the permission levels based on the perm_spec JSON.

        the mapping looks like:
        {
            'users': {
                'AnonymousUser': ['view'],
                <username>: ['perm1','perm2','perm3'],
                <username2>: ['perm1','perm2','perm3']
                ...
            }
            'groups': [
                <groupname>: ['perm1','perm2','perm3'],
                <groupname2>: ['perm1','perm2','perm3'],
                ...
                ]
        }
        """
        if not created:
            remove_object_permissions(self)

            # default permissions for resource owner
            set_owner_permissions(self)

        # Anonymous User group
        if 'users' in perm_spec and "AnonymousUser" in perm_spec['users']:
            anonymous_group = Group.objects.get(name='anonymous')
            for perm in perm_spec['users']['AnonymousUser']:
                if self.polymorphic_ctype.name == 'layer' and perm in ('change_layer_data', 'change_layer_style',
                                                                       'add_layer', 'change_layer', 'delete_layer',):
                    assign_perm(perm, anonymous_group, self.layer)
                else:
                    assign_perm(perm, anonymous_group, self.get_self_resource())

        # Owner
        if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
            if self.polymorphic_ctype.name == 'layer':
                if not created:
                    purge_geofence_layer_rules(self.get_self_resource())
                perms = [
                    "view_resourcebase",
                    "change_layer_data",
                    "change_layer_style",
                    "change_resourcebase",
                    "change_resourcebase_permissions",
                    "download_resourcebase"]
                sync_geofence_with_guardian(self.layer, perms, user=self.owner)

        # All the other users
        if 'users' in perm_spec and len(perm_spec['users']) > 0:
            for user, perms in perm_spec['users'].items():
                _user = get_user_model().objects.get(username=user)
                if _user != self.owner and user != "AnonymousUser":
                    for perm in perms:
                        if self.polymorphic_ctype.name == 'layer' and perm in (
                                'change_layer_data', 'change_layer_style',
                                'add_layer', 'change_layer', 'delete_layer',):
                            assign_perm(perm, _user, self.layer)
                        else:
                            assign_perm(perm, _user, self.get_self_resource())

                    # Set the GeoFence Rules
                    if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                        if self.polymorphic_ctype.name == 'layer':
                            group_perms = None
                            if 'groups' in perm_spec and len(perm_spec['groups']) > 0:
                                group_perms = perm_spec['groups']
                            sync_geofence_with_guardian(self.layer, perms, user=_user, group_perms=group_perms)

        # All the other groups
        if 'groups' in perm_spec and len(perm_spec['groups']) > 0:
            for group, perms in perm_spec['groups'].items():
                _group = Group.objects.get(name=group)
                for perm in perms:
                    if self.polymorphic_ctype.name == 'layer' and perm in (
                            'change_layer_data', 'change_layer_style',
                            'add_layer', 'change_layer', 'delete_layer',):
                        assign_perm(perm, _group, self.layer)
                    else:
                        assign_perm(perm, _group, self.get_self_resource())

                # Set the GeoFence Rules
                if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                    if self.polymorphic_ctype.name == 'layer':
                        if _group and _group.name and _group.name == 'anonymous':
                            _group = None
                        sync_geofence_with_guardian(self.layer, perms, group=_group)

        # AnonymousUser
        if 'users' in perm_spec and len(perm_spec['users']) > 0:
            if "AnonymousUser" in perm_spec['users']:
                perms = perm_spec['users']["AnonymousUser"]
                for perm in perms:
                    if self.polymorphic_ctype.name == 'layer' and perm in (
                            'change_layer_data', 'change_layer_style',
                            'add_layer', 'change_layer', 'delete_layer',):
                        assign_perm(perm, _user, self.layer)
                    else:
                        assign_perm(perm, _user, self.get_self_resource())

                # Set the GeoFence Rules (user = None)
                if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                    if self.polymorphic_ctype.name == 'layer':
                        sync_geofence_with_guardian(self.layer, perms)

    def set_workflow_perms(self, approved=False, published=False):
        """
                          |  N/PUBLISHED   | PUBLISHED
          --------------------------------------------
            N/APPROVED    |     GM/OWR     |     -
            APPROVED      |   registerd    |    all
          --------------------------------------------
        """
        anonymous_group = Group.objects.get(name='anonymous')
        if approved:
            if groups_settings.AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME:
                _members_group_name = groups_settings.REGISTERED_MEMBERS_GROUP_NAME
                _members_group_group = Group.objects.get(name=_members_group_name)
                for perm in VIEW_PERMISSIONS:
                    assign_perm(perm,
                                _members_group_group, self.get_self_resource())

                # Set the GeoFence Rules (user = None)
                if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                    if self.polymorphic_ctype.name == 'layer':
                        sync_geofence_with_guardian(self.layer, VIEW_PERMISSIONS, group=_members_group_group)
            else:
                for perm in VIEW_PERMISSIONS:
                    assign_perm(perm,
                                anonymous_group, self.get_self_resource())

                # Set the GeoFence Rules (user = None)
                if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                    if self.polymorphic_ctype.name == 'layer':
                        sync_geofence_with_guardian(self.layer, VIEW_PERMISSIONS)

        if published:
            for perm in VIEW_PERMISSIONS:
                assign_perm(perm,
                            anonymous_group, self.get_self_resource())

            # Set the GeoFence Rules (user = None)
            if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                if self.polymorphic_ctype.name == 'layer':
                    sync_geofence_with_guardian(self.layer, VIEW_PERMISSIONS)
