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

    def _get_cache_key(self, resource_pk, user=None):
        """
        Generate consistent cache keys for resource permissions.

        Cache key format: "resource_perms:{resource_pk}:{user_identifier}"

        Where user_identifier can be:
        - user.pk: For authenticated users
        - "anonymous": For anonymous users
        - "__ALL__": For permission queries that don't specify a user (returns all permissions)

        Args:
            resource_pk: Primary key of the resource
            user: User instance, None for __ALL__ cache

        Returns:
            str: Cache key for the given resource and user combination
        """
        if user is None:
            identifier = "__ALL__"
        elif user.is_anonymous:
            identifier = "anonymous"
        else:
            identifier = str(user.pk)

        return f"resource_perms:{resource_pk}:{identifier}"

    def get_perms(
        self,
        instance,
        user=None,
        include_virtual=True,
        include_user_add_resource=False,
        use_cache=False,
        *args,
        **kwargs,
    ):
        """
        Return the payload with the permissions from the handlers.
        The permissions payload can be edited by each permissions handler.
        For example before return the payload, we can virtually remove perms
        to the resource
        include_user_add_resource -> If true add the add_resourcebase to the user perms if the user have it
        Use use_cache=True to enable caching for performance-critical operations
        """
        cache_key = None
        if use_cache:
            cache_key = self._get_cache_key(instance.pk, user)  # Generate cache key based on resource and user
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
        if user:
            payload = {"users": {user: instance.get_user_perms(user)}, "groups": {}}
        else:
            payload = instance.get_all_level_info()

        for handler in self.REGISTRY:
            payload = handler.get_perms(instance, payload, user, include_virtual=include_virtual, *args, **kwargs)

        if user:
            if include_user_add_resource and user.has_perm("base.add_resourcebase"):
                payload["users"][user].extend(["add_resourcebase"])
            if use_cache and cache_key:
                cache.set(cache_key, payload["users"][user], settings.PERMISSION_CACHE_EXPIRATION_TIME)
            return payload["users"][user]
        if use_cache and cache_key:
            cache.set(cache_key, payload, settings.PERMISSION_CACHE_EXPIRATION_TIME)
        return payload

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
