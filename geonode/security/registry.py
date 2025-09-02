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
from guardian.shortcuts import get_objects_for_user, get_objects_for_group, get_anonymous_user, get_group_perms
from django.contrib.auth.models import AnonymousUser as DjangoAnonymousUser
from geonode.security.permissions import PERMISSIONS, READ_ONLY_AFFECTED_PERMISSIONS
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from guardian.utils import get_user_obj_perms_model
from geonode.security.permissions import (
    VIEW_PERMISSIONS,
    ADMIN_PERMISSIONS,
    SERVICE_PERMISSIONS,
    DOWNLOAD_PERMISSIONS,
    DATASET_ADMIN_PERMISSIONS,
    DATASET_EDIT_DATA_PERMISSIONS,
    DATASET_EDIT_STYLE_PERMISSIONS,
)


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

    @classmethod
    def get_registry(cls):
        return PermissionsHandlerRegistry.REGISTRY

    def sanity_checks(self):
        for item in self.REGISTRY:
            self.__check_item(item)

    def user_has_perm(self, user, instance, perm, include_virtual=False):
        """
        Returns True if the user has the defined perm (permission)
        """
        return perm in self.get_perms(
            instance=instance, user=user, include_virtual=True, include_user_add_resource=True
        )

    def user_can_feature(self, user, resource):
        """
        Utility method to check if the user can set a resource as "featured" in the metadata
        By default only superuser/admins can do
        """
        from geonode.people.utils import user_is_manager_of_group

        if user.is_superuser:
            return True

        # Check if the user is a group manager
        is_manager = user_is_manager_of_group(user, resource.group)
        if is_manager:
            return True

        return False

    def user_can_approve(self, user, resource):
        """
        Utility method to check if the user can set a resource as "approved" in the metadata
        """
        from geonode.security.utils import AdvancedSecurityWorkflowManager

        ResourceGroupsAndMembersSet = AdvancedSecurityWorkflowManager.compute_resource_groups_and_members_set(
            resource.uuid, instance=resource, group=resource.group
        )
        is_superuser = user.is_superuser
        is_owner = user == resource.owner

        is_manager = user in ResourceGroupsAndMembersSet.managers

        can_change_metadata = user.has_perm("change_resourcebase_metadata", resource.get_self_resource())

        if is_superuser:
            return True
        elif AdvancedSecurityWorkflowManager.is_admin_moderate_mode():
            return is_manager and can_change_metadata
        else:
            return is_owner or is_manager or can_change_metadata

    def user_can_publish(self, user, resource):
        """
        Utility method to check if the user can set a resource as "published" in the metadata
        """
        from geonode.security.utils import AdvancedSecurityWorkflowManager

        ResourceGroupsAndMembersSet = AdvancedSecurityWorkflowManager.compute_resource_groups_and_members_set(
            resource.uuid, instance=resource, group=resource.group
        )
        is_superuser = user.is_superuser
        is_owner = user == resource.owner
        is_manager = user in ResourceGroupsAndMembersSet.managers

        if is_superuser:
            return True
        elif AdvancedSecurityWorkflowManager.is_manager_publish_mode():
            return is_manager
        else:
            return is_owner or is_manager

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
        permissions={},
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
        if isinstance(user, DjangoAnonymousUser):
            user = get_anonymous_user()

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
            payload = permissions or {
                "users": {user: instance.get_user_perms(user)},
                "groups": {group: list(get_group_perms(group, instance))},
            }
            for handler in self.REGISTRY:
                payload = handler.get_perms(instance, payload, user, include_virtual=include_virtual, *args, **kwargs)
            result = payload
        elif user:
            payload = {"users": {user: instance.get_user_perms(user)}, "groups": {}}
            for handler in self.REGISTRY:
                payload = handler.get_perms(instance, payload, user, include_virtual=include_virtual, *args, **kwargs)
            if include_user_add_resource and user.has_perm("base.add_resourcebase"):
                payload["users"][user].append("add_resourcebase")

            result = payload["users"][user]
        elif group:
            payload = permissions or {"users": {}, "groups": {group: list(get_group_perms(group, instance))}}
            for handler in self.REGISTRY:
                payload = handler.get_perms(instance, payload, user, include_virtual=include_virtual, *args, **kwargs)
            result = payload["groups"][group]
        else:
            payload = permissions or instance.get_all_level_info()
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
        from geonode.security.utils import AdvancedSecurityWorkflowManager

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

    def get_users_with_perms(self, obj):
        """
        Override of the Guardian get_users_with_perms
        """
        ctype = ContentType.objects.get_for_model(obj)
        ctype_resource_base = ContentType.objects.get_for_model(obj.get_self_resource())
        permissions = {}
        PERMISSIONS_TO_FETCH = VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS + ADMIN_PERMISSIONS + SERVICE_PERMISSIONS
        # include explicit permissions appliable to "subtype == 'vector'"
        if obj.subtype == "vector":
            PERMISSIONS_TO_FETCH += DATASET_ADMIN_PERMISSIONS
            for perm in Permission.objects.filter(
                codename__in=PERMISSIONS_TO_FETCH, content_type_id__in=[ctype.id, ctype_resource_base.id]
            ):
                permissions[perm.id] = perm.codename
        elif obj.subtype == "raster":
            PERMISSIONS_TO_FETCH += DATASET_EDIT_STYLE_PERMISSIONS
            for perm in Permission.objects.filter(
                codename__in=PERMISSIONS_TO_FETCH, content_type_id__in=[ctype.id, ctype_resource_base.id]
            ):
                permissions[perm.id] = perm.codename
        else:
            PERMISSIONS_TO_FETCH += DATASET_EDIT_DATA_PERMISSIONS
            for perm in Permission.objects.filter(codename__in=PERMISSIONS_TO_FETCH):
                permissions[perm.id] = perm.codename

        user_model = get_user_obj_perms_model(obj)
        users_with_perms = user_model.objects.filter(object_pk=obj.pk, permission_id__in=permissions).values(
            "user_id", "permission_id"
        )

        users = {}
        for item in users_with_perms:
            if item["user_id"] in users:
                users[item["user_id"]].append(permissions[item["permission_id"]])
            else:
                users[item["user_id"]] = [
                    permissions[item["permission_id"]],
                ]

        profiles = {}
        for profile in get_user_model().objects.filter(id__in=list(users.keys())):
            profiles[profile] = users[profile.id]

        return profiles

    def get_resources_with_perms(self, user, filter_options={}, shortcut_kwargs={}):
        """
        Returns resources a user has access to.
        """
        from geonode.security.utils import get_geoapp_subtypes
        from geonode.base.models import ResourceBase

        if settings.SKIP_PERMS_FILTER:
            resources = ResourceBase.objects.all()
        else:
            resources = get_objects_for_user(
                user, ["base.view_resourcebase", "base.change_resourcebase"], any_perm=True, **shortcut_kwargs
            )

        resources_with_perms = self.get_visible_resources(
            resources,
            user,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES,
            include_dirty=False,
        )

        if filter_options:
            if resources_with_perms and resources_with_perms.exists():
                if filter_options.get("title_filter"):
                    resources_with_perms = resources_with_perms.filter(
                        title__icontains=filter_options.get("title_filter")
                    )
                type_filters = []
                if filter_options.get("type_filter"):
                    _type_filter = filter_options.get("type_filter")
                    if _type_filter:
                        type_filters.append(_type_filter)
                    # get subtypes for geoapps
                    if _type_filter == "geoapp":
                        type_filters.extend(get_geoapp_subtypes())

                if type_filters:
                    resources_with_perms = resources_with_perms.filter(polymorphic_ctype__model__in=type_filters)

        return resources_with_perms

    def delete_resource_permissions_cache(self, instance, user_clear_cache=True, group_clear_cache=True, **kwargs):
        """
        Clear the cache for resource permissions when activity related to resource is performed.
        This ensures that permissions are recalculated on the next request.
        """

        from geonode.base.models import ResourceBase
        from geonode.people.models import Profile

        if isinstance(instance, ResourceBase):
            permissions = self.get_perms(instance=instance)
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

    def __check_item(self, item):
        """
        Ensure that the handler is a subclass of BasePermissionsHandler
        """
        if not isinstance(item, BasePermissionsHandler):
            raise Exception(f"Handler {item} is not a subclass of BasePermissionsHandler")

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


permissions_registry = PermissionsHandlerRegistry()
