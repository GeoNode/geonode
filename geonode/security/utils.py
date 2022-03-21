#########################################################################
#
# Copyright (C) 2018 OSGeo
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
from itertools import chain

from django.apps import apps
from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission
from guardian.utils import get_user_obj_perms_model
from guardian.shortcuts import get_objects_for_user

from geonode.groups.conf import settings as groups_settings
from geonode.security.permissions import (
    PermSpecCompact,
    VIEW_PERMISSIONS,
    ADMIN_PERMISSIONS,
    SERVICE_PERMISSIONS,
    DOWNLOAD_PERMISSIONS,
    DOWNLOADABLE_RESOURCES,
    BASIC_MANAGE_PERMISSIONS,
    DATASET_ADMIN_PERMISSIONS,
    DATASET_EDIT_DATA_PERMISSIONS,
    DATASET_EDIT_STYLE_PERMISSIONS,
    DATA_EDITABLE_RESOURCES_SUBTYPES)

logger = logging.getLogger(__name__)


def get_visible_resources(queryset,
                          user,
                          request=None,
                          metadata_only=False,
                          admin_approval_required=False,
                          unpublished_not_visible=False,
                          private_groups_not_visibile=False):
    # Get the list of objects the user has access to
    from geonode.groups.models import GroupProfile

    is_admin = user.is_superuser if user and user.is_authenticated else False
    anonymous_group = None
    public_groups = GroupProfile.objects.exclude(access="private").values('group')
    groups = []
    group_list_all = []
    try:
        group_list_all = user.group_list_all().values('group')
    except Exception:
        pass

    try:
        anonymous_group = Group.objects.get(name='anonymous')
        if anonymous_group and anonymous_group not in groups:
            groups.append(anonymous_group)
    except Exception:
        pass

    # Hide Dirty State Resources
    filter_set = queryset.filter(
        Q(dirty_state=False) & Q(metadata_only=metadata_only))

    if not is_admin:
        if user:
            _allowed_resources = get_objects_for_user(
                user,
                ['base.view_resourcebase', 'base.change_resourcebase'],
                any_perm=True)
            filter_set = filter_set.filter(id__in=_allowed_resources.values('id'))

        if admin_approval_required:
            if not user or not user.is_authenticated or user.is_anonymous:
                filter_set = filter_set.filter(
                    Q(is_published=True) |
                    Q(group__in=public_groups) |
                    Q(group__in=groups)
                ).exclude(is_approved=False)

        # Hide Unpublished Resources to Anonymous Users
        if unpublished_not_visible:
            if not user or not user.is_authenticated or user.is_anonymous:
                filter_set = filter_set.exclude(is_published=False)

        # Hide Resources Belonging to Private Groups
        if private_groups_not_visibile:
            private_groups = GroupProfile.objects.filter(access="private").values('group')
            if user and user.is_authenticated:
                filter_set = filter_set.exclude(
                    Q(group__in=private_groups) & ~(
                        Q(owner__username__iexact=str(user)) | Q(group__in=group_list_all))
                )
            else:
                filter_set = filter_set.exclude(group__in=private_groups)

    return filter_set


def get_users_with_perms(obj):
    """
    Override of the Guardian get_users_with_perms
    """
    from .permissions import (
        VIEW_PERMISSIONS,
        DOWNLOAD_PERMISSIONS,
        ADMIN_PERMISSIONS,
        SERVICE_PERMISSIONS,
        DATASET_ADMIN_PERMISSIONS,
        DATASET_EDIT_STYLE_PERMISSIONS)
    ctype = ContentType.objects.get_for_model(obj)
    permissions = {}
    PERMISSIONS_TO_FETCH = VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS + ADMIN_PERMISSIONS + SERVICE_PERMISSIONS
    # include explicit permissions appliable to "subtype == 'vector'"
    if obj.subtype == 'vector':
        PERMISSIONS_TO_FETCH += DATASET_ADMIN_PERMISSIONS
        for perm in Permission.objects.filter(codename__in=PERMISSIONS_TO_FETCH, content_type_id=ctype.id):
            permissions[perm.id] = perm.codename
    elif obj.subtype == 'raster':
        PERMISSIONS_TO_FETCH += DATASET_EDIT_STYLE_PERMISSIONS
        for perm in Permission.objects.filter(codename__in=PERMISSIONS_TO_FETCH, content_type_id=ctype.id):
            permissions[perm.id] = perm.codename
    else:
        PERMISSIONS_TO_FETCH += DATASET_EDIT_DATA_PERMISSIONS
        for perm in Permission.objects.filter(codename__in=PERMISSIONS_TO_FETCH):
            permissions[perm.id] = perm.codename

    user_model = get_user_obj_perms_model(obj)
    users_with_perms = user_model.objects.filter(object_pk=obj.pk,
                                                 permission_id__in=permissions).values('user_id', 'permission_id')

    users = {}
    for item in users_with_perms:
        if item['user_id'] in users:
            users[item['user_id']].append(permissions[item['permission_id']])
        else:
            users[item['user_id']] = [permissions[item['permission_id']], ]

    profiles = {}
    for profile in get_user_model().objects.filter(id__in=list(users.keys())):
        profiles[profile] = users[profile.id]

    return profiles


def perms_as_set(perm) -> set:
    return perm if isinstance(perm, set) else set(perm if isinstance(perm, list) else [perm])


def get_resources_with_perms(user, filter_options={}, shortcut_kwargs={}):
    """
    Returns resources a user has access to.
    """

    from geonode.base.models import ResourceBase

    if settings.SKIP_PERMS_FILTER:
        resources = ResourceBase.objects.all()
    else:
        resources = get_objects_for_user(
            user,
            ['base.view_resourcebase', 'base.change_resourcebase'],
            any_perm=True,
            **shortcut_kwargs
        )

    resources_with_perms = get_visible_resources(
        resources,
        user,
        admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
        unpublished_not_visible=settings.RESOURCE_PUBLISHING,
        private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)

    if filter_options:
        if resources_with_perms and resources_with_perms.count() > 0:
            if filter_options.get('title_filter'):
                resources_with_perms = resources_with_perms.filter(
                    title__icontains=filter_options.get('title_filter')
                )
            type_filters = []
            if filter_options.get('type_filter'):
                _type_filter = filter_options.get('type_filter')
                if _type_filter:
                    type_filters.append(_type_filter)
                # get subtypes for geoapps
                if _type_filter == 'geoapp':
                    type_filters.extend(get_geoapp_subtypes())

            if type_filters:
                resources_with_perms = resources_with_perms.filter(
                    polymorphic_ctype__model__in=type_filters
                )

    return resources_with_perms


def get_geoapp_subtypes():
    """
    Returns a list of geoapp subtypes.
    eg ['geostory']
    """

    from geonode.geoapps.models import GeoApp

    subtypes = []
    for label, app in apps.app_configs.items():
        if hasattr(app, 'type') and app.type == 'GEONODE_APP':
            if hasattr(app, 'default_model'):
                _model = apps.get_model(label, app.default_model)
                if issubclass(_model, GeoApp):
                    subtypes.append(_model.__name__.lower())
    return subtypes


def skip_registered_members_common_group(user_group):
    _members_group_name = groups_settings.REGISTERED_MEMBERS_GROUP_NAME
    if (settings.RESOURCE_PUBLISHING or settings.ADMIN_MODERATE_UPLOADS) and \
            _members_group_name == user_group.name:
        return True
    return False


def get_user_groups(owner):
    """
    Returns all the groups belonging to the "owner"
    """
    user_groups = Group.objects.filter(
        name__in=owner.groupmember_set.all().values_list("group__slug", flat=True))
    return user_groups


def get_user_visible_groups(user, include_public_invite: bool = False):
    """
    Retrieves all the groups accordingly to the following conditions:
    - The user is member of
    - The group is public
    """
    from geonode.groups.models import GroupProfile

    metadata_author_groups = []
    if user.is_superuser or user.is_staff:
        metadata_author_groups = GroupProfile.objects.all()
    else:
        if include_public_invite:
            group_profile_queryset = GroupProfile.objects.exclude(
                access="private")
        else:
            group_profile_queryset = GroupProfile.objects.exclude(
                access="private").exclude(access="public-invite")
        try:
            all_metadata_author_groups = chain(
                user.group_list_all(),
                group_profile_queryset)
        except Exception:
            all_metadata_author_groups = group_profile_queryset
        [metadata_author_groups.append(item) for item in all_metadata_author_groups
            if item not in metadata_author_groups]
    return metadata_author_groups


class AdvancedSecurityWorkflowManager:

    @staticmethod
    def is_group_private_mode():
        return settings.GROUP_PRIVATE_RESOURCES

    @staticmethod
    def is_manager_publish_mode():
        return settings.RESOURCE_PUBLISHING

    @staticmethod
    def is_admin_moderate_mode():
        return settings.ADMIN_MODERATE_UPLOADS

    @staticmethod
    def is_auto_publishing_workflow():
        """
          **AUTO PUBLISHING**
            - `RESOURCE_PUBLISHING = False`
            - `ADMIN_MODERATE_UPLOADS = False`

            - When user creates a resource:
              - OWNER gets all the owner permissions (publish resource included)
              - ANONYMOUS can view and download
            - No change to the Group Manager is applied
        """
        return not settings.RESOURCE_PUBLISHING and not settings.ADMIN_MODERATE_UPLOADS

    @staticmethod
    def is_simple_publishing_workflow():
        """
          **SIMPLE PUBLISHING**
            - `RESOURCE_PUBLISHING = True` (Autopublishing is disabled)
            - `ADMIN_MODERATE_UPLOADS = False`

            - When user creates a resource:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` INCLUDED)
              - Group MANAGERS of the user's groups will get the owner permissions (`publish_resource` EXCLUDED)
              - Group MEMBERS of the user's groups will get the `view_resourcebase`, `download_resourcebase` permission
              - ANONYMOUS can not view and download if the resource is not published

            - When resource has a group assigned:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` INCLUDED)
              - Group MANAGERS of the *resource's group* will get the owner permissions (`publish_resource` EXCLUDED)
              - Group MEMBERS of the *resource's group* will get the `view_resourcebase`, `download_resourcebase` permission
        """
        return settings.RESOURCE_PUBLISHING and not settings.ADMIN_MODERATE_UPLOADS

    @staticmethod
    def is_advanced_workflow():
        """
          **ADVANCED WORKFLOW**
            - `RESOURCE_PUBLISHING = True`
            - `ADMIN_MODERATE_UPLOADS = True`

            - When user creates a resource:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` EXCLUDED)
              - Group MANAGERS of the user's groups will get the owner permissions (`publish_resource` INCLUDED)
              - Group MEMBERS of the user's groups will get the `view_resourcebase`, `download_resourcebase` permission
              - ANONYMOUS can not view and download if the resource is not published

            - When resource has a group assigned:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` EXCLUDED)
              - Group MANAGERS of the resource's group will get the owner permissions (`publish_resource` INCLUDED)
              - Group MEMBERS of the resource's group will get the `view_resourcebase`, `download_resourcebase` permission
        """
        return settings.RESOURCE_PUBLISHING and settings.ADMIN_MODERATE_UPLOADS

    @staticmethod
    def is_simplified_workflow():
        """
          **SIMPLIFIED WORKFLOW**
            - `RESOURCE_PUBLISHING = False`
            - `ADMIN_MODERATE_UPLOADS = True`

            - **NOTE**: Is it even possibile? when the resource is automatically published, can it be un-published?
            If this combination is not allowed, we should either stop the process when reading the settings or log a warning and force a safe combination.

            - When user creates a resource:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` INCLUDED)
              - Group MANAGERS of the user's groups will get the owner permissions (`publish_resource` INCLUDED)
              - Group MEMBERS of the user's group will get the `view_resourcebase`, `download_resourcebase` permission
              - ANONYMOUS can view and download
        """
        return not settings.RESOURCE_PUBLISHING and settings.ADMIN_MODERATE_UPLOADS

    @staticmethod
    def assignable_perm_condition(perm, resource_type):
        _assignable_perm_policy_condition = (perm in DOWNLOAD_PERMISSIONS and resource_type in DOWNLOADABLE_RESOURCES) or \
            (perm in DATASET_EDIT_DATA_PERMISSIONS and resource_type in DATA_EDITABLE_RESOURCES_SUBTYPES) or \
            (perm not in (DOWNLOAD_PERMISSIONS + DATASET_EDIT_DATA_PERMISSIONS))
        logger.debug(f" perm: {perm} - resource_type: {resource_type} --> assignable: {_assignable_perm_policy_condition}")
        return _assignable_perm_policy_condition

    @staticmethod
    def get_instance(uuid: str):
        from geonode.base.models import ResourceBase

        _resources = ResourceBase.objects.filter(uuid=uuid)
        _exists = _resources.count() == 1
        if _exists:
            return _resources.get()
        return None

    @staticmethod
    def set_group_member_permissions(user, group, role):

        def _handle_perms(perms=None):
            '''
            Internally the set_permissions function will automatically handle the permissions
            that needs to be assigned to re resource.
            Background at: https://github.com/GeoNode/geonode/pull/8145
            If the user is demoted, we assign by default at least the view and the download permission
            to the resource
            '''
            queryset = (
                get_objects_for_user(
                    user,
                    ["base.view_resourcebase", "base.change_resourcebase"],
                    any_perm=True)
                .filter(group=group.group)
                .exclude(owner=user)
            )
            # A.F.: By including 'group.resources()' here, we will look also for resources
            #       having permissions related to the current 'group' and not only the ones assigned
            #       to the 'group' through the metadata settings.
            # _resources = set([_r for _r in queryset.iterator()] + [_r for _r in group.resources()])
            _resources = queryset.iterator()
            for _r in _resources:
                perm_spec = _r.get_all_level_info()
                if perms:
                    if "users" not in perm_spec:
                        perm_spec["users"] = {}
                    perm_spec["users"][user] = perms
                # Let's the ResourceManager finally decide which are the correct security settings to apply
                _r.set_permissions(perm_spec)

        if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow():
            if role and role == "manager":
                _handle_perms(perms=VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS + BASIC_MANAGE_PERMISSIONS)
            else:
                _handle_perms(perms=VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS)

    @staticmethod
    def get_owner_permissions(uuid: str, /, instance=None, members: list = [], perm_spec: dict = {"users": {}, "groups": {}}) -> dict:
        """compute a perm_spec to assing all admin permissions to the owner"""
        _resource = instance or AdvancedSecurityWorkflowManager.get_instance(uuid)
        _perm_spec = copy.deepcopy(perm_spec)

        if _resource:
            _resource = _resource.get_real_instance()
            if _resource.polymorphic_ctype:
                # Owner & Manager Admin Perms
                admin_perms = VIEW_PERMISSIONS + ADMIN_PERMISSIONS
                if _resource.polymorphic_ctype.name in DOWNLOADABLE_RESOURCES:
                    admin_perms += DOWNLOAD_PERMISSIONS
                for perm in admin_perms:
                    if not settings.RESOURCE_PUBLISHING and not settings.ADMIN_MODERATE_UPLOADS:
                        _prev_perm = _perm_spec["users"].get(_resource.owner, []) if "users" in _perm_spec else []
                        _perm_spec["users"][_resource.owner] = set.union(perms_as_set(_prev_perm), perms_as_set(perm))
                    elif perm not in {'change_resourcebase_permissions', 'publish_resourcebase'}:
                        _prev_perm = _perm_spec["users"].get(_resource.owner, []) if "users" in _perm_spec else []
                        _perm_spec["users"][_resource.owner] = set.union(perms_as_set(_prev_perm), perms_as_set(perm))
                    if members:
                        for user in members:
                            _prev_perm = _perm_spec["users"].get(user, []) if "users" in _perm_spec else []
                            _perm_spec["users"][user] = set.union(perms_as_set(_prev_perm), perms_as_set(perm))

                # Set the GeoFence Owner Rule
                if _resource.polymorphic_ctype.name == 'dataset':
                    DATA_EDIT_PERMISSIONS = []
                    if _resource.get_real_instance().subtype == 'vector':
                        DATA_EDIT_PERMISSIONS = DATASET_ADMIN_PERMISSIONS
                    elif _resource.get_real_instance().subtype == 'raster':
                        DATA_EDIT_PERMISSIONS = DATASET_EDIT_STYLE_PERMISSIONS
                    for perm in DATA_EDIT_PERMISSIONS:
                        _prev_perm = _perm_spec["users"].get(_resource.owner, []) if "users" in _perm_spec else []
                        _perm_spec["users"][_resource.owner] = set.union(perms_as_set(_prev_perm), perms_as_set(perm))
                        if members:
                            for user in members:
                                _prev_perm = _perm_spec["users"].get(user, []) if "users" in _perm_spec else []
                                _perm_spec["users"][user] = set.union(perms_as_set(_prev_perm), perms_as_set(perm))

                if _resource.polymorphic_ctype.name == 'service':
                    for perm in SERVICE_PERMISSIONS:
                        _prev_perm = _perm_spec["users"].get(_resource.owner, []) if "users" in _perm_spec else []
                        _perm_spec["users"][_resource.owner] = set.union(perms_as_set(_prev_perm), perms_as_set(perm))
                        if members:
                            for user in members:
                                _prev_perm = _perm_spec["users"].get(user, []) if "users" in _perm_spec else []
                                _perm_spec["users"][user] = set.union(perms_as_set(_prev_perm), perms_as_set(perm))
        return _perm_spec

    @staticmethod
    def get_workflow_permissions(uuid: str, /, instance=None, permissions: dict = {}) -> dict:
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

        General Rules:
         - OWNER can always publish, except in the ADVANCED WORKFLOW
         - When the user is OWNER and MANAGER, the MANAGER wins!
         - Group MANAGERS have publish privs only when `ADMIN_MODERATE_UPLOADS` is True (no DATA EDIT perms assigned by default)
         - Group MEMBERS have always access to the resource, except for the AUTOPUBLISH, where everybody has access to it.
        """
        _resource = instance or AdvancedSecurityWorkflowManager.get_instance(uuid)

        _permissions = None
        if permissions:
            if PermSpecCompact.validate(permissions):
                _permissions = PermSpecCompact(copy.deepcopy(permissions), _resource).extended
            else:
                _permissions = copy.deepcopy(permissions)

        if _resource:
            perm_spec = _permissions or copy.deepcopy(_resource.get_all_level_info())

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
            perm_spec = _resource.fixup_perms(perm_spec)
            _resource_type = _resource.resource_type or _resource.polymorphic_ctype.name

            if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow():
                # compute advanced workflow permissions
                if _resource_type not in DOWNLOADABLE_RESOURCES:
                    view_perms = VIEW_PERMISSIONS
                else:
                    view_perms = VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS

                admin_perms = ADMIN_PERMISSIONS.copy()

                admin_nopub_perms = ADMIN_PERMISSIONS.copy()
                admin_nopub_perms.remove('publish_resourcebase')

                admin_restricted_perms = ADMIN_PERMISSIONS.copy()
                admin_restricted_perms.remove('publish_resourcebase')
                admin_restricted_perms.remove('change_resourcebase_permissions')

                anonymous_group = Group.objects.get(name='anonymous')
                registered_members_group_name = groups_settings.REGISTERED_MEMBERS_GROUP_NAME
                user_groups = Group.objects.filter(
                    name__in=_resource.owner.groupmember_set.all().values_list("group__slug", flat=True))
                member_group_perm, group_managers = _resource.get_group_managers(user_groups)

                # Handle the owner perms
                if _resource.owner:
                    prev_perms = perm_spec['users'].get(_resource.owner, []) if isinstance(perm_spec['users'], dict) else []
                    if AdvancedSecurityWorkflowManager.is_advanced_workflow():
                        perm_spec['users'][_resource.owner] = list(
                                    set(prev_perms + view_perms + admin_restricted_perms))
                    else:
                        perm_spec['users'][_resource.owner] = list(
                                    set(prev_perms + view_perms + admin_perms))

                # Handle the Group Managers perms
                if group_managers:
                    for group_manager in group_managers:
                        prev_perms = perm_spec['users'].get(group_manager, []) if isinstance(perm_spec['users'], dict) else []
                        # AF: Should be a manager being able to change the dataset data and style too by default?
                        #     For the time being let's give to the manager "management" perms only.
                        # if _resource.polymorphic_ctype.name == 'layer':
                        #     perm_spec['users'][group_manager] = list(
                        #         set(prev_perms + view_perms + ADMIN_PERMISSIONS + LAYER_ADMIN_PERMISSIONS))
                        # else:
                        if AdvancedSecurityWorkflowManager.is_simple_publishing_workflow():
                            perm_spec['users'][group_manager] = list(
                                set(prev_perms + view_perms + admin_nopub_perms))
                        else:
                            perm_spec['users'][group_manager] = list(
                                set(prev_perms + view_perms + admin_perms))

                # Handle the Group Members perms
                if member_group_perm:
                    for gr, perm in member_group_perm['groups'].items():
                        if gr != anonymous_group and gr.name != registered_members_group_name:
                            prev_perms = perm_spec['groups'].get(gr, []) if isinstance(perm_spec['groups'], dict) else []
                            perm_spec['groups'][gr] = list(set(prev_perms + perm))

                # Handle the Anoymous and other members perms
                if _resource.is_approved:
                    if getattr(groups_settings, 'AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME', False):
                        registered_members_group = Group.objects.get(name=registered_members_group_name)
                        prev_perms = perm_spec['groups'].get(registered_members_group, []) if isinstance(perm_spec['groups'], dict) else []
                        perm_spec['groups'][registered_members_group] = list(set(prev_perms + view_perms))
                    else:
                        prev_perms = perm_spec['groups'].get(anonymous_group, []) if isinstance(perm_spec['groups'], dict) else []
                        perm_spec['groups'][anonymous_group] = list(set(prev_perms + view_perms))

                if _resource.is_published:
                    prev_perms = perm_spec['groups'].get(anonymous_group, []) if isinstance(perm_spec['groups'], dict) else []
                    perm_spec['groups'][anonymous_group] = list(set(prev_perms + view_perms))
            else:
                # default permissions for resource owner
                perm_spec = AdvancedSecurityWorkflowManager.get_owner_permissions(_resource.uuid, perm_spec=perm_spec)

        return perm_spec
