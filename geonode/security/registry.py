#########################################################################
#
# Copyright (C) 2024 OSGeo
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
import operator
from django.conf import settings
from django.utils.module_loading import import_string
from geonode.security.handlers import BasePermissionsHandler, AdvancedSecurityWorkflowManager
from django.core.cache import cache
from django.db.models import Q
from django.contrib.auth.models import Group
from guardian.shortcuts import get_group_perms
from guardian.shortcuts import get_objects_for_user, get_objects_for_group
from guardian.shortcuts import get_anonymous_user
from django.contrib.contenttypes.models import ContentType
from functools import reduce

from geonode.security.permissions import (
    EDIT_PERMISSIONS,
    VIEW_PERMISSIONS,
    DOWNLOAD_PERMISSIONS,
    ADMIN_PERMISSIONS,
    SERVICE_PERMISSIONS,
    DATASET_ADMIN_PERMISSIONS,
    DATASET_EDIT_DATA_PERMISSIONS,
    DATASET_EDIT_STYLE_PERMISSIONS,
    PERMISSIONS,
    READ_ONLY_AFFECTED_PERMISSIONS,
)
from django.contrib.auth.models import Permission
from guardian.shortcuts import get_perms
from geonode.security.utils import can_approve, can_feature, can_publish, get_user_obj_perms_model


class PermissionsHandlerRegistry:

    REGISTRY = []

    def init_registry(self):
        self._register()
        self.sanity_checks()

    def add(self, module_path):
        item = import_string(module_path)()
        self.__check_item(item)
        self.REGISTRY.append(item)

    def remove(self, module_path):
        item = import_string(module_path)()
        self.__check_item(item)
        self.REGISTRY.remove(item)

    def reset(self):
        self.REGISTRY = []

    def sanity_checks(self):
        for item in self.REGISTRY:
            self.__check_item(item)

    def fixup_perms(self, instance, payload, include_virtual=True, *args, **kwargs):
        for handler in self.REGISTRY:
            payload = handler.fixup_perms(instance, payload, include_virtual=include_virtual, *args, **kwargs)
        return payload

    def get_db_perms_by_user(self, user):
        from geonode.base.models import Configuration

        perms = set()
        if user.is_superuser or user.is_staff:
            # return all permissions for admins
            perms.update(PERMISSIONS.values())

        user_groups = user.groups.values_list("name", flat=True)
        group_perms = (
            Permission.objects.filter(group__name__in=user_groups).distinct().values_list("codename", flat=True)
        )
        for p in group_perms:
            if p in PERMISSIONS:
                # return constant names defined by GeoNode
                perms.add(PERMISSIONS[p])
            else:
                # add custom permissions
                perms.add(p)

        # check READ_ONLY mode
        config = Configuration.load()
        if config.read_only:
            # exclude permissions affected by readonly
            perms = [perm for perm in perms if perm not in READ_ONLY_AFFECTED_PERMISSIONS]
        return list(perms)

    def get_perms(
        self,
        instance,
        user=None,
        include_virtual=True,
        include_user_add_resource=False,
        use_cache=False,
        group=None,
        *args,
        **kwargs,
    ):
        """
        Return the permissions for the specified user, group, or all permissions.

        Args:
            instance: Resource instance
            user: User instance
            group: Group instance
            include_virtual: Include virtual permissions
            include_user_add_resource: Add resourcebase permissions for users
            use_cache: Enable caching

        Returns:
            dict: Permissions payload or specific permissions list
        """
        cache_key = None
        if use_cache:
            cache_key = self._get_cache_key([instance.pk], [user] if user else None, [group] if group else None)
            if cache_key:
                if isinstance(cache_key, list):
                    user_cache_key, group_cache_key = cache_key
                    user_cached = cache.get(user_cache_key)
                    group_cached = cache.get(group_cache_key)

                    if user_cached is not None and group_cached is not None:
                        return {"users": {user: user_cached}, "groups": {group: group_cached}}
                else:
                    cached = cache.get(cache_key)
                    if cached is not None:
                        return cached

        if user and group:
            payload = {
                "users": {user: list(self._calculate_perms(instance, user))},
                "groups": {group: list(get_group_perms(group, instance))},
            }
            for handler in self.REGISTRY:
                payload = handler.get_perms(instance, payload, user, include_virtual=include_virtual, *args, **kwargs)
            result = payload
        elif user:
            payload = {"users": {user: list(self._calculate_perms(instance, user))}, "groups": {}}
            for handler in self.REGISTRY:
                payload = handler.get_perms(instance, payload, user, include_virtual=include_virtual, *args, **kwargs)
            if include_user_add_resource and "add_resourcebase" in self.get_db_perms_by_user(user=user):
                payload["users"][user].append("add_resourcebase")

            result = payload["users"][user]
        elif group:
            payload = {"users": {}, "groups": {group: list(get_group_perms(group, instance))}}
            for handler in self.REGISTRY:
                payload = handler.get_perms(instance, payload, user, include_virtual=include_virtual, *args, **kwargs)
            result = payload["groups"][group]
        else:
            payload = instance.get_all_level_info()
            for handler in self.REGISTRY:
                payload = handler.get_perms(instance, payload, user, include_virtual=include_virtual, *args, **kwargs)
            result = payload

        if use_cache and isinstance(cache_key, list):
            if user_cache_key and group_cache_key:
                cache.set(user_cache_key, result["users"][user], settings.PERMISSION_CACHE_EXPIRATION_TIME)
                cache.set(group_cache_key, result["groups"][group], settings.PERMISSION_CACHE_EXPIRATION_TIME)
        elif use_cache and cache_key:
            cache.set(cache_key, result, settings.PERMISSION_CACHE_EXPIRATION_TIME)
        else:
            pass

        return result

    @classmethod
    def get_registry(cls):
        return PermissionsHandlerRegistry.REGISTRY

    def get_visible_resources(
        self,
        queryset,
        user,
        request=None,
        metadata_only=False,
        admin_approval_required=False,
        unpublished_not_visible=False,
        private_groups_not_visibile=False,
        include_dirty=False,
    ):
        # Get the list of objects the user has access to
        from geonode.groups.models import GroupProfile

        is_admin = user.is_superuser if user and user.is_authenticated else False
        anonymous_group = None
        public_groups = GroupProfile.objects.exclude(access="private").values("group")
        groups = []
        group_list_all = []
        try:
            group_list_all = user.group_list_all().values("group")
        except Exception:
            pass

        try:
            anonymous_group = Group.objects.get(name="anonymous")
            if anonymous_group and anonymous_group not in groups:
                groups.append(anonymous_group)
        except Exception:
            pass

        if metadata_only is not None:
            # Hide Dirty State Resources
            queryset = queryset.filter(metadata_only=metadata_only)

        if not include_dirty:
            queryset = queryset.filter(dirty_state=False)

        if not is_admin:
            if user:
                _allowed_resources = get_objects_for_user(
                    user, ["base.view_resourcebase", "base.change_resourcebase"], any_perm=True
                )
                queryset = queryset.filter(id__in=_allowed_resources.values("id"))

            if admin_approval_required and not AdvancedSecurityWorkflowManager.is_simplified_workflow():
                if not user or not user.is_authenticated or user.is_anonymous:
                    queryset = queryset.filter(
                        Q(is_published=True) | Q(group__in=public_groups) | Q(group__in=groups)
                    ).exclude(is_approved=False)

            # Hide Unpublished Resources to Anonymous Users
            if unpublished_not_visible:
                if not user or not user.is_authenticated or user.is_anonymous:
                    queryset = queryset.exclude(is_published=False)

            # Hide Resources Belonging to Private Groups
            if private_groups_not_visibile:
                private_groups = GroupProfile.objects.filter(access="private").values("group")
                if user and user.is_authenticated:
                    queryset = queryset.exclude(
                        Q(group__in=private_groups)
                        & ~(Q(owner__username__iexact=str(user)) | Q(group__in=group_list_all))
                    )
                else:
                    queryset = queryset.exclude(group__in=private_groups)

        return queryset

    def delete_resource_permissions_cache(self, instance, user_clear_cache=True, group_clear_cache=True, **kwargs):
        """
        Clear the cache for resource permissions when activity related to resource is performed.
        This ensures that permissions are recalculated on the next request.
        """

        from geonode.base.models import ResourceBase
        from geonode.people.models import Profile

        if isinstance(instance, ResourceBase):
            permissions = permissions_registry.get_perms(instance=instance)
            users = Profile.objects.filter(
                Q(groups__in=permissions["groups"].keys()) | Q(id__in=[x.id for x in permissions["users"].keys()])
            ).distinct()

            cache_keys = self._get_cache_key(
                resource_pks=[instance.pk],
                users=users if user_clear_cache else None,
                groups=permissions["groups"].keys() if group_clear_cache else None,
                remove_all_cache=True,  # This will ensure that the __ALL__ cache key is included
            )
            self._clear_cache_keys(cache_keys if cache_keys else [])

        elif isinstance(instance, Group):
            group_users = instance.user_set.all()
            resource_pks_with_perms = [
                resource.pk for resource in get_objects_for_group(instance, ["base.view_resourcebase"], any_perm=True)
            ]

            cache_keys = self._get_cache_key(
                resource_pks=resource_pks_with_perms,
                users=group_users if user_clear_cache else None,
                groups=[instance] if group_clear_cache else None,
            )
            self._clear_cache_keys(cache_keys if cache_keys else [])

        elif isinstance(instance, Profile):
            resources = get_objects_for_user(instance, "base.view_resourcebase")
            resource_pks = [resource.pk for resource in resources]

            cache_keys = self._get_cache_key(
                resource_pks=resource_pks,
                users=[instance] if user_clear_cache else None,
                groups=instance.groups.all() if group_clear_cache else None,
            )

            self._clear_cache_keys(cache_keys if cache_keys else [])

        else:
            pass

    def user_has_perm(self, user, instance, perm, include_virtual=False):
        """
        Returns True if the user has the defined perm (permission)
        """
        return perm in self.get_perms(
            instance=instance, user=user, include_virtual=True, include_user_add_resource=True
        )

    def _calculate_perms(self, instance, user):
        def _calculate(instance, user):
            # To avoid circular import
            from geonode.base.models import Configuration
            from geonode.layers.models import Dataset

            config = Configuration.load()
            ctype = ContentType.objects.get_for_model(instance)
            ctype_resource_base = ContentType.objects.get_for_model(instance.get_self_resource())

            PERMISSIONS_TO_FETCH = (
                VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS + ADMIN_PERMISSIONS + SERVICE_PERMISSIONS + EDIT_PERMISSIONS
            )
            # include explicit permissions appliable to "subtype == 'vector'"

            if instance.subtype == "raster":
                PERMISSIONS_TO_FETCH += DATASET_EDIT_STYLE_PERMISSIONS
            elif isinstance(instance.get_real_instance(), Dataset):
                # remote layers are included, since https://github.com/GeoNode/geonode/issues/13011
                # introduces an "optimistic" approach to editing remote layers
                PERMISSIONS_TO_FETCH += DATASET_ADMIN_PERMISSIONS

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

        perms = _calculate(instance, user)

        if getattr(instance, "get_real_instance", None):
            perms = perms.union(_calculate(instance.get_real_instance(), user))

        if getattr(instance, "get_self_resource", None):
            perms = perms.union(_calculate(instance.get_self_resource(), user))

        perms_as_list = list(set(perms))

        if user.is_anonymous:
            # anonymous cannot feature/approve or pusblish, we can return here the perms
            return perms_as_list

        if not perms_as_list:
            return perms_as_list

        return perms_as_list

    def _register(self):
        for module_path in settings.PERMISSIONS_HANDLERS:
            self.add(module_path)

    def _clear_cache_keys(self, cache_keys):
        """Clear cache keys."""
        if cache_keys:
            if isinstance(cache_keys, str):
                cache.delete(cache_keys)
            elif isinstance(cache_keys, list):
                cache.delete_many(cache_keys)
            else:
                raise TypeError(f"Expected str or list, got {type(cache_keys)}")

    def _get_cache_key(self, resource_pks, users=None, groups=None, remove_all_cache=False):
        """
        Generate cache keys for resource permissions.

        Args:
            resource_pks: List of resource primary keys
            users: Optional list of users to generate keys for
            groups: Optional list of groups to generate keys for
            remove_all_cache: If True, includes the __ALL__ cache key
        """
        cache_keys = []
        for pk in resource_pks:
            if users:
                for user in users:
                    user_identifier = (
                        "anonymous"
                        if user.is_anonymous or user.username == "AnonymousUser" or user == get_anonymous_user()
                        else f"user:{user.pk}"
                    )
                    cache_keys.append(f"resource_perms:{pk}:{user_identifier}")

            if groups:
                for group in groups:
                    cache_keys.append(f"resource_perms:{pk}:group:{group.pk}")

            if not users and not groups or remove_all_cache:
                cache_keys.append(f"resource_perms:{pk}:__ALL__")

        return cache_keys if len(cache_keys) > 1 else cache_keys[0] if cache_keys else None

    def __check_item(self, item):
        """
        Ensure that the handler is a subclass of BasePermissionsHandler
        """
        if not isinstance(item, BasePermissionsHandler):
            raise Exception(f"Handler {item} is not a subclass of BasePermissionsHandler")


permissions_registry = PermissionsHandlerRegistry()
