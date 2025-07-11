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
from django.conf import settings
from django.utils.module_loading import import_string
from geonode.security.handlers import BasePermissionsHandler
from django.core.cache import cache
from django.db.models import Q
from django.contrib.auth.models import Group
from guardian.shortcuts import get_group_perms
from guardian.shortcuts import get_objects_for_user, get_objects_for_group


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

    def _register(self):
        for module_path in settings.PERMISSIONS_HANDLERS:
            self.add(module_path)

    def sanity_checks(self):
        for item in self.REGISTRY:
            self.__check_item(item)

    def __check_item(self, item):
        """
        Ensure that the handler is a subclass of BasePermissionsHandler
        """
        if not isinstance(item, BasePermissionsHandler):
            raise Exception(f"Handler {item} is not a subclass of BasePermissionsHandler")

    def fixup_perms(self, instance, payload, include_virtual=True, *args, **kwargs):
        for handler in self.REGISTRY:
            payload = handler.fixup_perms(instance, payload, include_virtual=include_virtual, *args, **kwargs)
        return payload

    def delete_resource_permissions_cache(self, instance, user_clear_cache=False, group_clear_cache=False, **kwargs):
        """
        Clear the cache for resource permissions when a resource is deleted.
        This ensures that permissions are recalculated on the next request.
        """

        from geonode.base.models import ResourceBase
        from geonode.people.models import Profile

        def _generate_cache_keys(
            resource_pks, users=None, groups=None, include_user_cache=True, include_group_cache=True
        ):
            """Generate cache keys for given resources, users, and groups."""
            cache_keys = []

            for pk in resource_pks:
                # User-specific cache keys
                if include_user_cache and users:
                    cache_keys.extend([f"resource_perms:{pk}:user:{user.pk}" for user in users])

                # Group-specific cache keys
                if include_group_cache and groups:
                    cache_keys.extend([f"resource_perms:{pk}:group:{group.pk}" for group in groups])

                cache_keys.extend([f"resource_perms:{pk}:__ALL__", f"resource_perms:{pk}:anonymous"])

            return cache_keys

        def _clear_cache_keys(cache_keys):
            """Clear cache keys."""
            if cache_keys:
                cache.delete_many(cache_keys)

        clear_user_cache = user_clear_cache or (not user_clear_cache and not group_clear_cache)
        clear_group_cache = group_clear_cache or (not user_clear_cache and not group_clear_cache)

        if isinstance(instance, ResourceBase):
            permissions = permissions_registry.get_perms(instance=instance)
            users = Profile.objects.filter(
                Q(groups__in=permissions["groups"].keys()) | Q(id__in=[x.id for x in permissions["users"].keys()])
            ).distinct()

            cache_keys = _generate_cache_keys(
                resource_pks=[instance.pk],
                users=users if clear_user_cache else None,
                groups=permissions["groups"].keys() if clear_group_cache else None,
                include_user_cache=clear_user_cache,
                include_group_cache=clear_group_cache,
            )
            _clear_cache_keys(cache_keys)

        elif isinstance(instance, Group):
            group_users = instance.user_set.all()
            resource_pks_with_perms = [
                resource.pk
                for resource in get_objects_for_group(
                    instance, ["base.view_resourcebase", "base.change_resourcebase"], any_perm=True
                )
            ]

            cache_keys = _generate_cache_keys(
                resource_pks=resource_pks_with_perms,
                users=group_users if clear_user_cache else None,
                groups=[instance] if group_clear_cache else None,
                include_user_cache=clear_user_cache,
                include_group_cache=group_clear_cache,
            )

            _clear_cache_keys(cache_keys)

        elif isinstance(instance, Profile):
            resources = get_objects_for_user(instance, "base.view_resourcebase")
            resource_pks = [resource.pk for resource in resources]

            user_groups = instance.groups.all() if group_clear_cache else None

            cache_keys = _generate_cache_keys(
                resource_pks=resource_pks,
                users=[instance] if clear_user_cache else None,
                groups=user_groups,
                include_user_cache=clear_user_cache,
                include_group_cache=group_clear_cache,
            )
            _clear_cache_keys(cache_keys)

        else:
            pass

    def _get_cache_key(self, resource_pk, user=None, group=None):
        """
        Generate consistent cache keys for resource permissions.

        Cache key format: "resource_perms:{resource_pk}:{identifier}"

        Where identifier can be:
        - user.pk: For authenticated users
        - "anonymous": For anonymous users
        - group.pk: For group-specific requests
        - "__ALL__": For permission queries that don't specify user or group

        Args:
            resource_pk: Primary key of the resource
            user: User instance, None if not querying user perms
            group: Group instance, None if not querying group perms

        Returns:
            str: Cache key for the given resource and user/group combination
        """
        if user is not None:
            if user.is_anonymous:
                identifier = "anonymous"
            else:
                identifier = f"user:{user.pk}"
        elif group is not None:
            identifier = f"group:{group.pk}"
        else:
            identifier = "__ALL__"

        return f"resource_perms:{resource_pk}:{identifier}"

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

        Priority: user perms > group perms

        Args:
            instance: Resource instance
            user: User instance (takes priority over group)
            group: Group instance (used only if user is None)
            include_virtual: Include virtual permissions
            include_user_add_resource: Add resourcebase permissions for users
            use_cache: Enable caching

        Returns:
            dict: Permissions payload or specific permissions list
        """
        cache_key = None
        if use_cache:
            cache_key = self._get_cache_key(instance.pk, user, group)
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        if user and group:
            user_perms = self.get_perms(
                instance,
                user=user,
                include_virtual=include_virtual,
                include_user_add_resource=include_user_add_resource,
                use_cache=use_cache,
                *args,
                **kwargs,
            )

            group_perms = self.get_perms(
                instance, group=group, include_virtual=include_virtual, use_cache=use_cache, *args, **kwargs
            )

            return {"users": {user: user_perms}, "groups": {group: group_perms}}

        if user:
            payload = {"users": {user: instance.get_user_perms(user)}, "groups": {}}
        elif group:
            payload = {"users": {}, "groups": {group: get_group_perms(group, instance)}}
        else:
            payload = instance.get_all_level_info()

        for handler in self.REGISTRY:
            payload = handler.get_perms(instance, payload, user, include_virtual=include_virtual, *args, **kwargs)

        if user:
            if include_user_add_resource and user.has_perm("base.add_resourcebase"):
                payload["users"][user].append("add_resourcebase")

            result = payload["users"][user]
        elif group:
            result = payload["groups"][group]
        else:
            result = payload

        if use_cache and cache_key:
            cache.set(cache_key, result, settings.PERMISSION_CACHE_EXPIRATION_TIME)

        return result

    def user_has_perm(self, user, instance, perm, include_virtual=False):
        """
        Returns True if the user has the defined perm (permission)
        """
        return perm in self.get_perms(
            instance=instance, user=user, include_virtual=True, include_user_add_resource=True
        )

    @classmethod
    def get_registry(cls):
        return PermissionsHandlerRegistry.REGISTRY


permissions_registry = PermissionsHandlerRegistry()
