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
import operator

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
    GeofenceLayerRulesUnitOfWork,
    GeofenceLayerAdapter,
    _get_gf_services,
    toggle_layer_cache,
    get_user_geolimits,
    get_users_with_perms,
    set_owner_permissions,
    get_user_obj_perms_model,
    remove_object_permissions,
    sync_geofence_with_guardian,
    skip_registered_members_common_group
)

logger = logging.getLogger("geonode.security.models")


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
        """
        Remove all the permissions except for the owner and assign the
        view permission to the anonymous group
        """
        geofence_adapter = GeofenceLayerAdapter(self.get_self_resource())
        try:
            with GeofenceLayerRulesUnitOfWork(geofence_adapter) as geofence_uow:
                with transaction.atomic():
                    remove_object_permissions(self, purge=False, geofence_uow=geofence_uow)

                    # default permissions for anonymous users
                    anonymous_group, created = Group.objects.get_or_create(name='anonymous')

                    # default permissions for owner
                    _owner = owner or self.owner
                    user_groups = Group.objects.filter(
                        name__in=_owner.groupmember_set.all().values_list("group__slug", flat=True))
                    obj_group_managers = []
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

                    if self.polymorphic_ctype.name == 'layer':
                        # only for layer owner
                        assign_perm('change_layer_data', _owner, self)
                        assign_perm('change_layer_style', _owner, self)

                # Fixup GIS Backend Security Rules Accordingly
                if self.polymorphic_ctype.name == 'layer':
                    if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                        if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):

                            if not created:
                                geofence_uow.purge_rules()

                            # Owner & Managers
                            perms = [
                                "view_resourcebase",
                                "change_layer_data",
                                "change_layer_style",
                                "change_resourcebase",
                                "change_resourcebase_permissions",
                                "download_resourcebase"]
                            sync_geofence_with_guardian(self.layer, perms, user=_owner, geofence_uow=geofence_uow)
                            for _group_manager in obj_group_managers:
                                sync_geofence_with_guardian(self.layer, perms, user=_group_manager, geofence_uow=geofence_uow)
                            for user_group in user_groups:
                                if not skip_registered_members_common_group(user_group):
                                    sync_geofence_with_guardian(self.layer, perms, group=user_group, geofence_uow=geofence_uow)

                            # Anonymous
                            perms = ["view_resourcebase"]
                            if anonymous_can_view:
                                sync_geofence_with_guardian(self.layer, perms, user=None, group=None, geofence_uow=geofence_uow)

                            perms = ["download_resourcebase"]
                            if anonymous_can_download:
                                sync_geofence_with_guardian(self.layer, perms, user=None, group=None, geofence_uow=geofence_uow)

                            # Force GeoFence rules cache invalidation
                            geofence_uow.set_invalidate_cache()
                        else:
                            self.set_dirty_state()
        except Exception as e:
            geofence_adapter.rollback()
            raise GeoNodeException(e)

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
        geofence_adapter = GeofenceLayerAdapter(self.get_self_resource())
        try:
            with GeofenceLayerRulesUnitOfWork(geofence_adapter) as geofence_uow:
                with transaction.atomic():
                    remove_object_permissions(self, purge=False, geofence_uow=geofence_uow)

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

                    # AnonymousUser
                    if 'users' in perm_spec and len(perm_spec['users']) > 0:
                        if "AnonymousUser" in perm_spec['users']:
                            _user = get_anonymous_user()
                            perms = perm_spec['users']["AnonymousUser"]
                            for perm in perms:
                                if self.polymorphic_ctype.name == 'layer' and perm in (
                                        'change_layer_data', 'change_layer_style',
                                        'add_layer', 'change_layer', 'delete_layer',):
                                    assign_perm(perm, _user, self.layer)
                                else:
                                    assign_perm(perm, _user, self.get_self_resource())

                # Fixup GIS Backend Security Rules Accordingly
                if self.polymorphic_ctype.name == 'layer':
                    if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                        if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):

                            if not created:
                                geofence_uow.purge_rules()

                            _disable_cache = []

                            # Owner
                            perms = [
                                "view_resourcebase",
                                "change_layer_data",
                                "change_layer_style",
                                "change_resourcebase",
                                "change_resourcebase_permissions",
                                "download_resourcebase"]
                            sync_geofence_with_guardian(self.layer, perms, user=self.owner, geofence_uow=geofence_uow)
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
                                    sync_geofence_with_guardian(self.layer, perms, user=_user, group_perms=group_perms, geofence_uow=geofence_uow)
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
                                    sync_geofence_with_guardian(self.layer, perms, group=_group, geofence_uow=geofence_uow)
                                    gf_services = _get_gf_services(self.layer, perms)
                                    _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(self.layer, None, _group, gf_services)
                                    _disable_cache.append(_disable_layer_cache)

                            # AnonymousUser
                            if 'users' in perm_spec and len(perm_spec['users']) > 0:
                                if "AnonymousUser" in perm_spec['users']:
                                    _user = get_anonymous_user()
                                    perms = perm_spec['users']["AnonymousUser"]
                                    sync_geofence_with_guardian(self.layer, perms, geofence_uow=geofence_uow)
                                    gf_services = _get_gf_services(self.layer, perms)
                                    _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(self.layer, _user, None, gf_services)
                                    _disable_cache.append(_disable_layer_cache)

                            # Force GeoFence rules cache invalidation
                            geofence_uow.set_invalidate_cache()

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
                                toggle_layer_cache(
                                    f'{_layer_workspace}:{self.layer.name}',
                                    enable=True,
                                    filters=filters,
                                    formats=formats,
                                    geofence_uow=geofence_uow
                                )
                        else:
                            self.set_dirty_state()
        except Exception as e:
            geofence_adapter.rollback()
            raise GeoNodeException(e)

    def set_workflow_perms(self, approved=False, published=False):
        """
                          |  N/PUBLISHED   | PUBLISHED
          --------------------------------------------
            N/APPROVED    |     GM/OWR     |     -
            APPROVED      |   registerd    |    all
          --------------------------------------------
        """
        try:
            with transaction.atomic():
                anonymous_group = Group.objects.get(name='anonymous')
                members_group = None
                if approved:
                    if groups_settings.AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME:
                        _members_group_name = groups_settings.REGISTERED_MEMBERS_GROUP_NAME
                        members_group = Group.objects.get(name=_members_group_name)
                        for perm in VIEW_PERMISSIONS:
                            assign_perm(perm,
                                        members_group, self.get_self_resource())
                    else:
                        for perm in VIEW_PERMISSIONS:
                            assign_perm(perm,
                                        anonymous_group, self.get_self_resource())

                if published:
                    for perm in VIEW_PERMISSIONS:
                        assign_perm(perm,
                                    anonymous_group, self.get_self_resource())

                # Set the GeoFence Rules (user = None)
                if approved or published:
                    if self.polymorphic_ctype.name == 'layer':
                        if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                            if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
                                if approved and members_group:
                                    sync_geofence_with_guardian(self.layer, VIEW_PERMISSIONS, group=members_group)
                                else:
                                    sync_geofence_with_guardian(self.layer, VIEW_PERMISSIONS)
                            else:
                                self.set_dirty_state()
        except Exception as e:
            raise GeoNodeException(e)

    def get_user_perms(self, user):
        """
        Returns a list of permissions a user has on a given resource
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
