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

import copy
import json
import logging
import operator
import traceback

from functools import reduce

from django.db.models import Q
from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from guardian.shortcuts import (
    assign_perm,
    get_anonymous_user,
    get_groups_with_perms,
    get_perms
)

from geonode import GeoNodeException
from geonode.utils import get_layer_workspace
from geonode.groups.models import GroupProfile
from geonode.groups.conf import settings as groups_settings

from .permissions import (
    ADMIN_PERMISSIONS,
    LAYER_ADMIN_PERMISSIONS,
    VIEW_PERMISSIONS,
    SERVICE_PERMISSIONS
)

from .utils import (
    _get_gf_services,
    toggle_layer_cache,
    get_user_geolimits,
    get_users_with_perms,
    set_owner_permissions,
    get_user_obj_perms_model,
    remove_object_permissions,
    purge_geofence_layer_rules,
    sync_geofence_with_guardian,
    set_geofence_invalidate_cache,
    skip_registered_members_common_group
)

logger = logging.getLogger(__name__)


class PermissionLevelError(Exception):
    pass


class PermissionLevelMixin:

    """
    Mixin for adding "Permission Level" methods
    to a model class -- eg role systems where a
    user has exactly one assigned role with respect to
    an object representing an "access level"
    """

    def get_all_level_info(self):
        """
        Translates the current object guardian perms into a JSON-like "perm_spec" object in the form:
        {
            'users': {
                <Profile AnonymousUser>: ['view'],
                <Profile username>: ['perm1','perm2','perm3'],
                <Profile username2>: ['perm1','perm2','perm3']
                ...
            }
            'groups': [
                <Group groupname>: ['perm1','perm2','perm3'],
                <Group groupname2>: ['perm1','perm2','perm3'],
                ...
                ]
        }
        """
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
        # Remove duplicated perms if any
        if info:
            for _k, _v in info.items():
                for _kk, _vv in info[_k].items():
                    if _vv and isinstance(_vv, list):
                        info[_k][_kk] = list(set(_vv))
        return info

    def get_self_resource(self):
        """
        Returns the "ResourceBase" associated to this "object".
        """
        try:
            if hasattr(self, "resourcebase_ptr_id"):
                return self.resourcebase_ptr
        except ObjectDoesNotExist:
            pass
        return self

    def get_group_managers(self, user_groups):
        """
        Given the groups belonging to a "user", this method returns a tuple containing:
         - The "groups" perms spec with resource access permissions (at least VIEW ones)
         - The list of "group managers" of the groups above
        """
        obj_group_managers = []
        perm_spec = {"groups": {}}
        if user_groups:
            for _user_group in user_groups:
                if not skip_registered_members_common_group(Group.objects.get(name=_user_group)):
                    try:
                        _group_profile = GroupProfile.objects.get(slug=_user_group)
                        managers = _group_profile.get_managers()
                        if managers:
                            for manager in managers:
                                if manager not in obj_group_managers and not manager.is_superuser:
                                    obj_group_managers.append(manager)
                    except GroupProfile.DoesNotExist:
                        tb = traceback.format_exc()
                        logger.debug(tb)

        # assign view permissions to group resources
        if self.group and settings.RESOURCE_PUBLISHING:
            perm_spec['groups'][self.group] = VIEW_PERMISSIONS

        for x in self.owner.groupmember_set.all():
            if settings.RESOURCE_PUBLISHING and x.group.slug != groups_settings.REGISTERED_MEMBERS_GROUP_NAME:
                perm_spec['groups'][x.group.group] = VIEW_PERMISSIONS

        return perm_spec, obj_group_managers

    def assign_perm_specs(self, perm_spec):
        """
        Given a "perm_spec" assigns the permissions accordingly through the guardian shortcuts.

        This one also makes sure the "owner" has always the "edit" permissions on its own resource and takes care of
        refreshing the GeoFence rules if needed (i.e. the resource is a geospatial Layer).
        """
        try:
            with transaction.atomic():
                remove_object_permissions(self, purge=False)
                set_owner_permissions(self)

                # Anonymous User group
                if 'users' in perm_spec and ("AnonymousUser" in perm_spec['users'] or get_anonymous_user() in perm_spec['users']):
                    anonymous_user = "AnonymousUser" if "AnonymousUser" in perm_spec['users'] else get_anonymous_user()
                    anonymous_group = Group.objects.get(name='anonymous')
                    for perm in perm_spec['users'][anonymous_user]:
                        if self.polymorphic_ctype.name == 'layer' and perm in ('change_layer_data', 'change_layer_style',
                                                                               'add_layer', 'change_layer', 'delete_layer',):
                            assign_perm(perm, anonymous_group, self.layer)
                        else:
                            assign_perm(perm, anonymous_group, self.get_self_resource())

                # All the other users
                if 'users' in perm_spec and len(perm_spec['users']) > 0:
                    for user, perms in perm_spec['users'].items():
                        _user = user if isinstance(user, get_user_model()) else get_user_model().objects.get(username=user)
                        if _user != self.owner and user != "AnonymousUser" and user != get_anonymous_user():
                            for perm in perms:
                                if self.polymorphic_ctype.name == 'layer' and perm in (
                                        'change_layer_data', 'change_layer_style',
                                        'add_layer', 'change_layer', 'delete_layer',):
                                    assign_perm(perm, _user, self.layer)
                                else:
                                    assign_perm(perm, _user, self.get_self_resource())

                # All the other groups
                if 'groups' in perm_spec and len(perm_spec['groups']) > 0:
                    for group, perms in perm_spec['groups'].items():
                        _group = group if isinstance(group, Group) else Group.objects.get(name=group)
                        for perm in perms:
                            if self.polymorphic_ctype.name == 'layer' and perm in (
                                    'change_layer_data', 'change_layer_style',
                                    'add_layer', 'change_layer', 'delete_layer',):
                                assign_perm(perm, _group, self.layer)
                            else:
                                assign_perm(perm, _group, self.get_self_resource())

                # AnonymousUser
                if 'users' in perm_spec and len(perm_spec['users']) > 0:
                    if "AnonymousUser" in perm_spec['users'] or get_anonymous_user() in perm_spec['users']:
                        _user = get_anonymous_user()
                        anonymous_user = "AnonymousUser" if "AnonymousUser" in perm_spec['users'] else get_anonymous_user()
                        perms = perm_spec['users'][anonymous_user]
                        for perm in perms:
                            if self.polymorphic_ctype.name == 'layer' and perm in (
                                    'change_layer_data', 'change_layer_style',
                                    'add_layer', 'change_layer', 'delete_layer',):
                                assign_perm(perm, _user, self.layer)
                            else:
                                assign_perm(perm, _user, self.get_self_resource())

                # Fixup GIS Backend Security Rules Accordingly
                self.fixup_geofence_rules(perm_spec)
        except Exception as e:
            raise GeoNodeException(e)

    def fixup_geofence_rules(self, perm_spec):
        """
        Clean up and set again the set of rules on GeoFence for this resource (if it is a Layer)
        """
        if self.polymorphic_ctype.name == 'layer':
            if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):

                    purge_geofence_layer_rules(self.get_self_resource())

                    _disable_cache = []

                    # Owner
                    perms = [
                        "view_resourcebase",
                        "change_layer_data",
                        "change_layer_style",
                        "change_resourcebase",
                        "change_resourcebase_permissions",
                        "download_resourcebase"]
                    sync_geofence_with_guardian(self.layer, perms, user=self.owner)
                    gf_services = _get_gf_services(self.layer, perms)
                    _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(self.layer, self.owner, None, gf_services)
                    _disable_cache.append(_disable_layer_cache)

                    # All the other users
                    if 'users' in perm_spec and len(perm_spec['users']) > 0:
                        for user, perms in perm_spec['users'].items():
                            _user = get_user_model().objects.get(username=user)
                            group_perms = None
                            if 'groups' in perm_spec and len(perm_spec['groups']) > 0:
                                group_perms = perm_spec['groups']
                            sync_geofence_with_guardian(self.layer, perms, user=_user, group_perms=group_perms)
                            gf_services = _get_gf_services(self.layer, perms)
                            _group = list(group_perms.keys())[0] if group_perms else None
                            _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(self.layer, _user, _group, gf_services)
                            _disable_cache.append(_disable_layer_cache)

                    # All the other groups
                    if 'groups' in perm_spec and len(perm_spec['groups']) > 0:
                        for group, perms in perm_spec['groups'].items():
                            _group = Group.objects.get(name=group)
                            if _group and _group.name and _group.name == 'anonymous':
                                _group = None
                            sync_geofence_with_guardian(self.layer, perms, group=_group)
                            gf_services = _get_gf_services(self.layer, perms)
                            _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(self.layer, None, _group, gf_services)
                            _disable_cache.append(_disable_layer_cache)

                    # AnonymousUser
                    if 'users' in perm_spec and len(perm_spec['users']) > 0:
                        if "AnonymousUser" in perm_spec['users'] or get_anonymous_user() in perm_spec['users']:
                            _user = get_anonymous_user()
                            anonymous_user = "AnonymousUser" if "AnonymousUser" in perm_spec['users'] else get_anonymous_user()
                            perms = perm_spec['users'][anonymous_user]
                            sync_geofence_with_guardian(self.layer, perms)
                            gf_services = _get_gf_services(self.layer, perms)
                            _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(self.layer, _user, None, gf_services)
                            _disable_cache.append(_disable_layer_cache)

                    # Force GeoFence rules cache invalidation
                    set_geofence_invalidate_cache()

                    # Invalidate GWC Cache if Geo-limits have been activated
                    if _disable_cache:
                        if any(_disable_cache):
                            filters = None
                            formats = None
                        else:
                            filters = [{
                                "styleParameterFilter": {
                                    "STYLES": ""
                                }
                            }]
                            formats = [
                                'application/json;type=utfgrid',
                                'image/gif',
                                'image/jpeg',
                                'image/png',
                                'image/png8',
                                'image/vnd.jpeg-png',
                                'image/vnd.jpeg-png8'
                            ]
                        _layer_workspace = get_layer_workspace(self.layer)
                        toggle_layer_cache(f'{_layer_workspace}:{self.layer.name}', enable=True, filters=filters, formats=formats)
                else:
                    self.set_dirty_state()

    def set_default_permissions(self, owner=None):
        """
        Removes all the permissions except for the owner and assign the
        view permission to the anonymous group.
        """
        # default permissions for anonymous users
        anonymous_group, created = Group.objects.get_or_create(name='anonymous')

        if not anonymous_group:
            raise Exception("Could not acquire 'anonymous' Group.")

        perm_spec = copy.deepcopy(self.get_all_level_info())
        if "users" not in perm_spec:
            perm_spec["users"] = {}
        if "groups" not in perm_spec:
            perm_spec["groups"] = {}

        # default permissions for owner and owner's groups
        _owner = owner or self.owner
        user_groups = Group.objects.filter(
            name__in=_owner.groupmember_set.all().values_list("group__slug", flat=True))

        # Anonymous
        anonymous_can_view = settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION
        if anonymous_can_view:
            perm_spec["groups"][anonymous_group] = ['view_resourcebase']
        else:
            for user_group in user_groups:
                if not skip_registered_members_common_group(user_group):
                    perm_spec["groups"][user_group] = ['view_resourcebase']

        anonymous_can_download = settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION
        if anonymous_can_download:
            perm_spec["groups"][anonymous_group] = ['view_resourcebase', 'download_resourcebase']
        else:
            for user_group in user_groups:
                if not skip_registered_members_common_group(user_group):
                    perm_spec["groups"][user_group] = ['view_resourcebase', 'download_resourcebase']

        # Fixup Advanced Workflow permissions
        perm_spec = self.get_workflow_perms(perm_spec)
        self.assign_perm_specs(perm_spec)

    def set_permissions(self, perm_spec=None):
        """
        Sets an object's the permission levels based on the perm_spec JSON.

        the mapping looks like:
        {
            'users': {
                'AnonymousUser': ['view'],
                'username': ['perm1','perm2','perm3'],
                'username2': ['perm1','perm2','perm3']
                ...
            },
            'groups': [
                'groupname': ['perm1','perm2','perm3'],
                'groupname2': ['perm1','perm2','perm3'],
                ...
            ]
        }
        """
        # Fixup Advanced Workflow permissions
        prev_perm_spec = copy.deepcopy(self.get_all_level_info())
        perm_spec = self.get_workflow_perms(perm_spec)
        # Avoid setting the permissions if nothing changed
        if not self.compare_perms(prev_perm_spec, perm_spec):
            self.assign_perm_specs(perm_spec)

    def compare_perms(self, prev_perm_spec, perm_spec):
        """
        Compare two perm_specs in the form
        {
            'users': {
                <Profile AnonymousUser>: ['view'],
                <Profile username>: ['perm1','perm2','perm3'],
                <Profile username2>: ['perm1','perm2','perm3']
                ...
            },
            'groups': [
                <Group groupname>: ['perm1','perm2','perm3'],
                <Group groupname2>: ['perm1','perm2','perm3'],
                ...
            ]
        }
        """
        if "users" in prev_perm_spec:
            if "users" in perm_spec:
                if len(prev_perm_spec["users"]) != len(perm_spec["users"]):
                    return False
                else:
                    _users_iterator = prev_perm_spec["users"].items() if isinstance(prev_perm_spec["users"], dict) else prev_perm_spec["users"]
                    for _user, _perms in _users_iterator:
                        if sorted(_perms) != sorted(perm_spec["users"].get(_user, [])):
                            return False
            else:
                return False
        if "groups" in prev_perm_spec:
            if "groups" in perm_spec:
                if len(prev_perm_spec["groups"]) != len(perm_spec["groups"]):
                    return False
                else:
                    _groups_iterator = prev_perm_spec["groups"].items() if isinstance(prev_perm_spec["groups"], dict) else prev_perm_spec["groups"]
                    for _group, _perms in _groups_iterator:
                        if sorted(_perms) != sorted(perm_spec["groups"].get(_group, [])):
                            return False
            else:
                return False
        return True

    def fixup_perms(self, perm_spec):
        """
        Transform a perm_spec in the form
        {
            'users': {
                'AnonymousUser': ['view'],
                'username': ['perm1','perm2','perm3'],
                'username2': ['perm1','perm2','perm3']
                ...
            },
            'groups': [
                'groupname': ['perm1','perm2','perm3'],
                'groupname2': ['perm1','perm2','perm3'],
                ...
            ]
        }

        to the one in the form:
        {
            'users': {
                <Profile AnonymousUser>: ['view'],
                <Profile username>: ['perm1','perm2','perm3'],
                <Profile username2>: ['perm1','perm2','perm3']
                ...
            },
            'groups': [
                <Group groupname>: ['perm1','perm2','perm3'],
                <Group groupname2>: ['perm1','perm2','perm3'],
                ...
            ]
        }

        It also removes items with empty permissions, e.g.:
            'AnonymousUser': []  # the item will completely removed
        """
        perm_spec_fixed = copy.deepcopy(perm_spec)
        if "users" in perm_spec:
            _users_iterator = perm_spec["users"].items() if isinstance(perm_spec["users"], dict) else perm_spec["users"]
            for _user, _perms in _users_iterator:
                if not isinstance(_user, get_user_model()):
                    perm_spec_fixed["users"].pop(_user)
                    if _perms and get_user_model().objects.filter(username=_user).count() == 1:
                        perm_spec_fixed["users"][get_user_model().objects.get(username=_user)] = _perms
        if "groups" in perm_spec:
            _groups_iterator = perm_spec["groups"].items() if isinstance(perm_spec["groups"], dict) else perm_spec["groups"]
            for _group, _perms in _groups_iterator:
                if not isinstance(_group, Group):
                    perm_spec_fixed["groups"].pop(_group)
                    if _perms and Group.objects.filter(name=_group).count() == 1:
                        perm_spec_fixed["groups"][Group.objects.get(name=_group)] = _perms
        return perm_spec_fixed

    def get_workflow_perms(self, perm_spec=None):
        """
        Adapts the provided "perm_spec" accordingly to the following schema:

                          |  N/PUBLISHED   | PUBLISHED
          --------------------------------------------
            N/APPROVED    |     GM/OWR     |     -
            APPROVED      |   registerd    |    all
          --------------------------------------------

        It also adds Group Managers as "editors" to the "perm_spec" in the case:
         - The Advanced Workflow has been enabled
         - The Group Managers are missing from the provided "perm_spec"

        Advanced Workflow Settings:

            **Scenario 1**: Default values: **AUTO PUBLISH**
            - `RESOURCE_PUBLISHING = False`
              `ADMIN_MODERATE_UPLOADS = False`

            - When user creates a resource
            - OWNER gets all the owner permissions (publish resource included)
            - ANONYMOUS can view and download

            **Scenario 2**: **SIMPLE PUBLISHING**
            - `RESOURCE_PUBLISHING = True` (Autopublishing is disabled)
              `ADMIN_MODERATE_UPLOADS = False`

            - When user creates a resource
            - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` INCLUDED)
            - Group MANAGERS of the user's groups will get the owner permissions (`publish_resource` EXCLUDED)
            - Group MEMBERS of the user's groups will get the `view_resourcebase` permission
            - ANONYMOUS can not view and download if the resource is not published

            - When resource has a group assigned:
            - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` INCLUDED)
            - Group MANAGERS of the *resource's group* will get the owner permissions (`publish_resource` EXCLUDED)
            - Group MEMBERS of the *resource's group* will get the `view_resourcebase` permission

            **Scenario 3**: **ADVANCED WORKFLOW**
            - `RESOURCE_PUBLISHING = True`
              `ADMIN_MODERATE_UPLOADS = True`

            - When user creates a resource
            - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` EXCLUDED)
            - Group MANAGERS of the user's groups will get the owner permissions (`publish_resource` INCLUDED)
            - Group MEMBERS of the user's groups will get the `view_resourcebase` permission
            - ANONYMOUS can not view and download if the resource is not published

            - When resource has a group assigned:
            - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` EXCLUDED)
            - Group MANAGERS of the resource's group will get the owner permissions (`publish_resource` INCLUDED)
            - Group MEMBERS of the resource's group will get the `view_resourcebase` permission

            **Scenario 4**: **SIMPLE WORKFLOW**
            - `RESOURCE_PUBLISHING = False`
              `ADMIN_MODERATE_UPLOADS = True`

            - **NOTE**: Is it even possibile? when the resource is automatically published, can it be un-published?
            If this combination is not allowed, we should either stop the process when reading the settings or log a warning and force a safe combination.

            - When user creates a resource
            - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` INCLUDED)
            - Group MANAGERS of the user's groups will get the owner permissions (`publish_resource` INCLUDED)
            - Group MEMBERS of the user's group will get the `view_resourcebase` permission
            - ANONYMOUS can view and download

            Recap:
            - OWNER can always publish, except in the ADVANCED WORKFLOW
            - Group MANAGERS have publish privs only when `ADMIN_MODERATE_UPLOADS` is True (no DATA EDIT perms assigned by default)
            - Group MEMBERS have always access to the resource, except for the AUTOPUBLISH, where everybody has access to it.
        """
        perm_spec = perm_spec or copy.deepcopy(self.get_all_level_info())

        # Sanity checks
        if isinstance(perm_spec, str):
            perm_spec = json.loads(perm_spec)

        if "users" not in perm_spec:
            perm_spec["users"] = {}
        elif isinstance(perm_spec["users"], list):
            _users = {}
            for _item in perm_spec["users"]:
                _users[_item[0]] = _item[1]
            perm_spec["users"] = _users

        if "groups" not in perm_spec:
            perm_spec["groups"] = {}
        elif isinstance(perm_spec["groups"], list):
            _groups = {}
            for _item in perm_spec["groups"]:
                _groups[_item[0]] = _item[1]
            perm_spec["groups"] = _groups

        # Make sure we're dealing with "Profile"s and "Group"s...
        perm_spec = self.fixup_perms(perm_spec)

        if settings.ADMIN_MODERATE_UPLOADS or settings.RESOURCE_PUBLISHING:
            # permissions = self._resolve_resource_permissions(resource=self, permissions=perm_spec)
            # default permissions for resource owner and group managers
            anonymous_group = Group.objects.get(name='anonymous')
            registered_members_group_name = groups_settings.REGISTERED_MEMBERS_GROUP_NAME
            user_groups = Group.objects.filter(
                name__in=self.owner.groupmember_set.all().values_list("group__slug", flat=True))
            member_group_perm, group_managers = self.get_group_managers(user_groups)

            if group_managers:
                for group_manager in group_managers:
                    prev_perms = perm_spec['users'].get(group_manager, []) if isinstance(perm_spec['users'], dict) else []
                    # AF: Should be a manager being able to change the dataset data and style too by default?
                    #     For the time being let's give to the manager "management" perms only.
                    # if self.polymorphic_ctype.name == 'layer':
                    #     perm_spec['users'][group_manager] = list(
                    #         set(prev_perms + VIEW_PERMISSIONS + ADMIN_PERMISSIONS + LAYER_ADMIN_PERMISSIONS))
                    # else:
                    perm_spec['users'][group_manager] = list(
                        set(prev_perms + VIEW_PERMISSIONS + ADMIN_PERMISSIONS))

            if member_group_perm:
                for gr, perm in member_group_perm['groups'].items():
                    if gr != anonymous_group and gr.name != registered_members_group_name:
                        prev_perms = perm_spec['groups'].get(gr, []) if isinstance(perm_spec['groups'], dict) else []
                        perm_spec['groups'][gr] = list(set(prev_perms + perm))

            if self.is_approved:
                if groups_settings.AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME:
                    registered_members_group = Group.objects.get(name=registered_members_group_name)
                    prev_perms = perm_spec['groups'].get(registered_members_group, []) if isinstance(perm_spec['groups'], dict) else []
                    perm_spec['groups'][registered_members_group] = list(set(prev_perms + VIEW_PERMISSIONS))
                else:
                    prev_perms = perm_spec['groups'].get(anonymous_group, []) if isinstance(perm_spec['groups'], dict) else []
                    perm_spec['groups'][anonymous_group] = list(set(prev_perms + VIEW_PERMISSIONS))

            if self.is_published:
                prev_perms = perm_spec['groups'].get(anonymous_group, []) if isinstance(perm_spec['groups'], dict) else []
                perm_spec['groups'][anonymous_group] = list(set(prev_perms + VIEW_PERMISSIONS))

        return perm_spec

    def get_user_perms(self, user):
        """
        Returns a list of permissions a user has on a given resource.
        """
        # To avoid circular import
        from geonode.base.models import Configuration

        config = Configuration.load()
        ctype = ContentType.objects.get_for_model(self)
        PERMISSIONS_TO_FETCH = VIEW_PERMISSIONS + ADMIN_PERMISSIONS + LAYER_ADMIN_PERMISSIONS + SERVICE_PERMISSIONS

        resource_perms = Permission.objects.filter(
            codename__in=PERMISSIONS_TO_FETCH,
            content_type_id=ctype.id
        ).values_list('codename', flat=True)

        # Don't filter for admin users
        if not user.is_superuser:
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
            if user.is_superuser:
                resource_perms = resource_perms.exclude(query)
            else:
                perm_objects = Permission.objects.filter(codename__in=resource_perms)
                resource_perms = perm_objects.exclude(query).values_list('codename', flat=True)

        return resource_perms

    def user_can(self, user, permission):
        """
        Checks if a has a given permission to the resource.
        """
        resource = self.get_self_resource()
        user_perms = self.get_user_perms(user).union(resource.get_user_perms(user))

        if permission not in user_perms:
            # TODO cater for permissions with syntax base.permission_codename
            # eg 'base.change_resourcebase'
            return False

        return True
