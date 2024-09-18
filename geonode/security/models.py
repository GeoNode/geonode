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
import logging
import operator
import traceback

from functools import reduce

from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from guardian.shortcuts import get_perms, get_groups_with_perms, get_anonymous_user

from geonode.groups.models import GroupProfile
from geonode.groups.conf import settings as groups_settings
from geonode.security.utils import get_user_groups, AdvancedSecurityWorkflowManager

from .permissions import (
    VIEW_PERMISSIONS,
    DOWNLOAD_PERMISSIONS,
    ADMIN_PERMISSIONS,
    SERVICE_PERMISSIONS,
    DATASET_ADMIN_PERMISSIONS,
    DATASET_EDIT_DATA_PERMISSIONS,
    DATASET_EDIT_STYLE_PERMISSIONS,
)

from .utils import get_users_with_perms, get_user_obj_perms_model, skip_registered_members_common_group

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
        groups = get_groups_with_perms(resource, attach_perms=True)

        info = {"users": users, "groups": groups}

        try:
            if hasattr(self, "dataset"):
                info_dataset = {
                    "users": get_users_with_perms(self.dataset),
                    "groups": get_groups_with_perms(self.dataset, attach_perms=True),
                }
                for user in info_dataset["users"]:
                    if user in info["users"]:
                        info["users"][user] = info["users"][user] + info_dataset["users"][user]
                    else:
                        info["users"][user] = info_dataset["users"][user]
                for group in info_dataset["groups"]:
                    if group in info["groups"]:
                        info["groups"][group] = list(
                            dict.fromkeys(info["groups"][group] + info_dataset["groups"][group])
                        )
                    else:
                        info["groups"][group] = info_dataset["groups"][group]
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)

        for _k, _v in info.items():
            for _kk in list(_v):
                # Remove AnonymousUser if set for some reason (legacy code)
                if _kk == get_anonymous_user():
                    logger.warning(
                        "Guardian permisions for AnonymouUser on resource {resource.id} were found in the DB, which is unexpected"
                    )
                    del info[_k][_kk]
                    continue
                _vv = _v[_kk]
                if _vv and isinstance(_vv, list):
                    # Remove duplicated perms
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

    def get_group_managers(self, group=None):
        """
        Given the groups belonging to a "user", this method returns a tuple containing:
         - The "groups" perms spec with resource access permissions (at least VIEW ones)
         - The list of "group managers" of the groups above
        """
        obj_groups = []
        obj_group_managers = []
        if group:
            user_groups = get_user_groups(self.owner, group=group)
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

        if self.group:
            obj_groups.append(self.group)
        for x in self.owner.groupmember_set.all():
            if x.group.slug != groups_settings.REGISTERED_MEMBERS_GROUP_NAME:
                obj_groups.append(x.group.group)
                managers = x.group.get_managers()
                if managers:
                    for manager in managers:
                        if manager not in obj_group_managers and not manager.is_superuser:
                            obj_group_managers.append(manager)

        return list(set(obj_groups)), list(set(obj_group_managers))

    def set_default_permissions(self, owner=None, created=False):
        """
        Removes all the permissions except for the owner and assign the
        view permission to the anonymous group.
        """
        from geonode.resource.manager import resource_manager

        # default permissions for anonymous users
        anonymous_group, _ = Group.objects.get_or_create(name="anonymous")

        if not anonymous_group:
            raise Exception("Could not acquire 'anonymous' Group.")

        perm_spec = copy.deepcopy(self.get_all_level_info())
        if "users" not in perm_spec:
            perm_spec["users"] = {}
        if "groups" not in perm_spec:
            perm_spec["groups"] = {}

        # default permissions for owner and owner's groups
        _owner = owner or self.owner
        user_groups = Group.objects.filter(name__in=_owner.groupmember_set.values_list("group__slug", flat=True))

        # Anonymous
        anonymous_can_view = settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION
        if anonymous_can_view:
            perm_spec["groups"][anonymous_group] = ["view_resourcebase"]
        else:
            for user_group in user_groups:
                # if aswm.is_auto_publishing_workflow() is False, means that at least one config of the advanced workflow
                # is set, which means that users group get view_permissions
                if (
                    not skip_registered_members_common_group(user_group)
                    and not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow()
                ):
                    perm_spec["groups"][user_group] = ["view_resourcebase"]

        anonymous_can_download = settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION
        if anonymous_can_download:
            perm_spec["groups"][anonymous_group] = ["view_resourcebase", "download_resourcebase"]
        else:
            for user_group in user_groups:
                # if aswm.is_auto_publishing_workflow() is False, means that at least one config of the advanced workflow
                # is set, which means that users group get view_permissions
                if (
                    not skip_registered_members_common_group(user_group)
                    and not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow()
                ):
                    perm_spec["groups"][user_group] = ["view_resourcebase", "download_resourcebase"]

        AdvancedSecurityWorkflowManager.handle_moderated_uploads(self.uuid, instance=self)
        return resource_manager.set_permissions(
            self.uuid, instance=self, owner=owner, permissions=perm_spec, created=created
        )

    def set_permissions(self, perm_spec=None, created=False, approval_status_changed=False, group_status_changed=False):
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
        from geonode.resource.manager import resource_manager

        return resource_manager.set_permissions(
            self.uuid,
            instance=self,
            permissions=perm_spec,
            created=created,
            approval_status_changed=approval_status_changed,
            group_status_changed=group_status_changed,
        )

    def handle_moderated_uploads(self):
        AdvancedSecurityWorkflowManager.handle_moderated_uploads(self.uuid, instance=self)

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
                    _users_iterator = (
                        prev_perm_spec["users"].items()
                        if isinstance(prev_perm_spec["users"], dict)
                        else prev_perm_spec["users"]
                    )
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
                    _groups_iterator = (
                        prev_perm_spec["groups"].items()
                        if isinstance(prev_perm_spec["groups"], dict)
                        else prev_perm_spec["groups"]
                    )
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
            _groups_iterator = (
                perm_spec["groups"].items() if isinstance(perm_spec["groups"], dict) else perm_spec["groups"]
            )
            for _group, _perms in _groups_iterator:
                if not isinstance(_group, Group):
                    perm_spec_fixed["groups"].pop(_group)
                    if _perms and Group.objects.filter(name=_group).count() == 1:
                        perm_spec_fixed["groups"][Group.objects.get(name=_group)] = _perms
        return perm_spec_fixed

    def get_user_perms(self, user):
        """
        Returns a list of permissions a user has on a given resource.
        """

        def calculate_perms(instance, user):
            # To avoid circular import
            from geonode.base.models import Configuration

            config = Configuration.load()
            ctype = ContentType.objects.get_for_model(instance)
            ctype_resource_base = ContentType.objects.get_for_model(instance.get_self_resource())

            PERMISSIONS_TO_FETCH = VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS + ADMIN_PERMISSIONS + SERVICE_PERMISSIONS
            # include explicit permissions appliable to "subtype == 'vector'"
            if instance.subtype in ["vector", "vector_time"]:
                PERMISSIONS_TO_FETCH += DATASET_ADMIN_PERMISSIONS
            elif instance.subtype == "raster":
                PERMISSIONS_TO_FETCH += DATASET_EDIT_STYLE_PERMISSIONS

            resource_perms = Permission.objects.filter(
                codename__in=PERMISSIONS_TO_FETCH, content_type_id__in=[ctype.id, ctype_resource_base.id]
            ).values_list("codename", flat=True)

            # Don't filter for admin users
            if not user.is_superuser:
                user_model = get_user_obj_perms_model(instance)
                user_resource_perms = user_model.objects.filter(
                    object_pk=instance.pk,
                    content_type_id__in=[ctype.id, ctype_resource_base.id],
                    user__username=str(user),
                    permission__codename__in=resource_perms,
                )
                # get user's implicit perms for anyone flag
                implicit_perms = get_perms(user, instance)
                # filter out implicit permissions unappliable to "subtype != 'vector'"
                if instance.subtype == "raster":
                    implicit_perms = list(set(implicit_perms) - set(DATASET_EDIT_DATA_PERMISSIONS))
                elif instance.subtype != "vector":
                    implicit_perms = list(set(implicit_perms) - set(DATASET_ADMIN_PERMISSIONS))

                resource_perms = user_resource_perms.union(
                    user_model.objects.filter(permission__codename__in=implicit_perms)
                ).values_list("permission__codename", flat=True)

            # filter out permissions for edit, change or publish if readonly mode is active
            perm_prefixes = ["change", "delete", "publish"]
            if config.read_only:
                clauses = (Q(codename__contains=prefix) for prefix in perm_prefixes)
                query = reduce(operator.or_, clauses)
                if user.is_superuser:
                    resource_perms = resource_perms.exclude(query)
                else:
                    perm_objects = Permission.objects.filter(codename__in=resource_perms)
                    resource_perms = perm_objects.exclude(query).values_list("codename", flat=True)
            return resource_perms

        perms = calculate_perms(self, user)

        if getattr(self, "get_real_instance", None):
            perms = perms.union(calculate_perms(self.get_real_instance(), user))

        if getattr(self, "get_self_resource", None):
            perms = perms.union(calculate_perms(self.get_self_resource(), user))

        perms_as_list = list(set(perms))

        if user.is_anonymous:
            # anonymous cannot feature/approve or pusblish, we can return here the perms
            return perms_as_list

        if not perms_as_list:
            return perms_as_list

        if user.can_feature(self):
            perms_as_list.append("feature_resourcebase")
        if user.can_approve(self):
            perms_as_list.append("approve_resourcebase")
        if user.can_publish(self):
            perms_as_list.append("publish_resourcebase")

        return perms_as_list

    def user_can(self, user, permission):
        """
        Checks if a has a given permission to the resource.
        """
        user_perms = self.get_user_perms(user)

        if permission not in user_perms:
            # TODO cater for permissions with syntax base.permission_codename
            # eg 'base.change_resourcebase'
            return False

        return True
