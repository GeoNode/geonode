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
import collections
from itertools import chain

from django.apps import apps
from django.db.models import Q
from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission
from guardian.utils import get_user_obj_perms_model
from guardian.models import (
    UserObjectPermission,
    GroupObjectPermission)
from guardian.shortcuts import (
    assign_perm,
    get_anonymous_user,
    get_objects_for_user)

from geonode.groups.conf import settings as groups_settings
from geonode.groups.models import GroupProfile
from geonode.security.permissions import (
    PermSpecCompact,
    VIEW_PERMISSIONS,
    ADMIN_PERMISSIONS,
    SERVICE_PERMISSIONS,
    DOWNLOAD_PERMISSIONS,
    DOWNLOADABLE_RESOURCES,
    LAYER_ADMIN_PERMISSIONS,
    LAYER_EDIT_DATA_PERMISSIONS,
    LAYER_EDIT_STYLE_PERMISSIONS,
    DATA_EDITABLE_RESOURCES_SUBTYPES,
    DATA_STYLABLE_RESOURCES_SUBTYPES)
from geonode.geoserver import security as gs_security

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

        if admin_approval_required and not AdvancedSecurityWorkflowManager.is_simplified_workflow():
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
    ctype = ContentType.objects.get_for_model(obj)
    permissions = {}
    PERMISSIONS_TO_FETCH = VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS + ADMIN_PERMISSIONS + SERVICE_PERMISSIONS
    try:
        # include explicit permissions appliable to "storeType == 'dataStore'"
        try:
            _resource = obj.get_real_instance()
        except Exception:
            _resource = obj
        if hasattr(_resource, 'storeType') and _resource.storeType == 'dataStore':
            PERMISSIONS_TO_FETCH += LAYER_ADMIN_PERMISSIONS
            for perm in Permission.objects.filter(codename__in=PERMISSIONS_TO_FETCH, content_type_id=ctype.id):
                permissions[perm.id] = perm.codename
        elif hasattr(_resource, 'storeType') and _resource.storeType == 'coverageStore':
            PERMISSIONS_TO_FETCH += LAYER_EDIT_STYLE_PERMISSIONS
            for perm in Permission.objects.filter(codename__in=PERMISSIONS_TO_FETCH, content_type_id=ctype.id):
                permissions[perm.id] = perm.codename
        else:
            PERMISSIONS_TO_FETCH += LAYER_EDIT_DATA_PERMISSIONS
            for perm in Permission.objects.filter(codename__in=PERMISSIONS_TO_FETCH):
                permissions[perm.id] = perm.codename
    except Exception as e:
        logger.debug(e)

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
        if resources_with_perms and resources_with_perms.exists():
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


def get_user_groups(owner, group=None):
    """
    Returns all the groups belonging to the "owner"
    """
    user_groups = Group.objects.filter(name__in=owner.groupmember_set.values_list("group__slug", flat=True))
    if group:
        user_groups = chain(user_groups, [group.group if hasattr(group, 'group') else group])
    return list(set(user_groups))


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


AdminViewPermissionsSet = collections.namedtuple('AdminViewPermissionsSet', [
    'admin_perms', 'view_perms'
])


ResourceGroupsAndMembersSet = collections.namedtuple('ResourceGroupsAndMembersSet', [
    'anonymous_group', 'registered_members_group', 'owner_groups', 'resource_groups', 'managers'
])


class AdvancedSecurityWorkflowManager:

    @staticmethod
    def is_anonymous_can_view():
        return settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION

    @staticmethod
    def is_anonymous_can_download():
        return settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION

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
    def is_allowed_to_approve(user, resource):
        ResourceGroupsAndMembersSet = AdvancedSecurityWorkflowManager.compute_resource_groups_and_members_set(
            resource.uuid, instance=resource, group=resource.group)
        is_superuser = user.is_superuser
        is_owner = user == resource.owner
        is_manager = user in ResourceGroupsAndMembersSet.managers

        can_change_metadata = user.has_perm(
            'change_resourcebase_metadata',
            resource.get_self_resource())

        if is_superuser:
            return True
        elif AdvancedSecurityWorkflowManager.is_admin_moderate_mode():
            return is_manager and can_change_metadata
        else:
            return is_owner or is_manager or can_change_metadata

    @staticmethod
    def is_allowed_to_publish(user, resource):
        ResourceGroupsAndMembersSet = AdvancedSecurityWorkflowManager.compute_resource_groups_and_members_set(
            resource.uuid, instance=resource, group=resource.group)
        is_superuser = user.is_superuser
        is_owner = user == resource.owner
        is_manager = user in ResourceGroupsAndMembersSet.managers

        can_publish = user.has_perm(
            'publish_resourcebase',
            resource.get_self_resource())

        if is_superuser:
            return True
        elif AdvancedSecurityWorkflowManager.is_manager_publish_mode():
            return is_manager and can_publish
        else:
            return is_owner or is_manager or can_publish

    @staticmethod
    def assignable_perm_condition(perm, resource_type):
        _assignable_perm_policy_condition = (perm in DOWNLOAD_PERMISSIONS and resource_type in DOWNLOADABLE_RESOURCES) or \
            (perm in LAYER_EDIT_DATA_PERMISSIONS and resource_type in DATA_EDITABLE_RESOURCES_SUBTYPES) or \
            (perm not in (DOWNLOAD_PERMISSIONS + LAYER_EDIT_DATA_PERMISSIONS))
        logger.debug(f" perm: {perm} - resource_type: {resource_type} --> assignable: {_assignable_perm_policy_condition}")
        return _assignable_perm_policy_condition

    @staticmethod
    def get_instance(uuid: str):
        from geonode.base.models import ResourceBase
        return ResourceBase.objects.filter(uuid=uuid).first()

    @staticmethod
    def compute_admin_and_view_permissions_set(uuid: str, /, instance=None) -> AdminViewPermissionsSet:
        """
        returns a copy of the ADMIN_PERMISSIONS and VIEW_PERMISISONS of a resource accordinlgy to:
         - The resource_type
         - The resource_subtype
        """
        _resource = instance or AdvancedSecurityWorkflowManager.get_instance(uuid)
        view_perms = []
        admin_perms = []
        if _resource.polymorphic_ctype:
            _resource_type = _resource.resource_type or _resource.polymorphic_ctype.name
            view_perms = VIEW_PERMISSIONS.copy()
            if _resource_type in DOWNLOADABLE_RESOURCES:
                view_perms += DOWNLOAD_PERMISSIONS.copy()

            admin_perms = ADMIN_PERMISSIONS.copy()
            if _resource.polymorphic_ctype.name == 'layer':
                try:
                    _resource_subtype = _resource.get_real_instance().storeType
                    if _resource_subtype in DATA_EDITABLE_RESOURCES_SUBTYPES:
                        admin_perms += LAYER_EDIT_DATA_PERMISSIONS.copy()
                    if _resource_subtype in DATA_STYLABLE_RESOURCES_SUBTYPES:
                        admin_perms += LAYER_EDIT_STYLE_PERMISSIONS.copy()
                except Exception as e:
                    logger.debug(e)

            if _resource.polymorphic_ctype.name == 'service':
                admin_perms += SERVICE_PERMISSIONS.copy()

        return AdminViewPermissionsSet(admin_perms, view_perms)

    @staticmethod
    def compute_resource_groups_and_members_set(uuid: str, /, instance=None, group=None) -> ResourceGroupsAndMembersSet:
        """
        returns a tuple containing:
         - The "Anonymous" Group
         - The "Registered Members" Group
         - The "Groups" belonging to the Resource Owner
         - The "managers" of the Groups affecting the Resource
         - The "members" of the Groups affecting the Resource
        """
        _resource = instance or AdvancedSecurityWorkflowManager.get_instance(uuid)
        anonymous_group = Group.objects.get(name='anonymous')
        registered_members_group = None
        registered_members_group_name = groups_settings.REGISTERED_MEMBERS_GROUP_NAME
        if getattr(groups_settings, 'AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME', False):
            registered_members_group = Group.objects.get(name=registered_members_group_name)
        user_groups = get_user_groups(_resource.owner, group=group)
        resource_groups, group_managers = _resource.get_group_managers(group=group)

        return ResourceGroupsAndMembersSet(anonymous_group, registered_members_group, user_groups, resource_groups, group_managers)

    @staticmethod
    def get_workflow_permissions(uuid: str, /, instance=None, perm_spec: dict = {"users": {}, "groups": {}}, created: bool = False,
                                 approval_status_changed: bool = False, group_status_changed: bool = False) -> dict:
        """
        Adapts the provided "perm_spec" accordingly to the following schema:
                                | RESOURCE_PUBLISHING | ADMIN_MODERATE_UPLOADS
          --------------------------------------------------------------------
            AUTO PUBLISH        |          X          |           X
            SIMPLE PUBLISHING   |          V          |           X
            SIMPLIFIED WORKFLOW |          X          |           V
            ADVANCED WORKFLOW   |          V          |           V

        General Rules:
         - OWNER can never publish, except in the AUTO_PUBLISHING workflow
         - MANAGERS can always "publish" the resource
         - MEMBERS can always "view" and "download" the resource
         - When the OWNER is also a MANAGER, the MANAGER wins! Therefore he can publish too
         - Others, except in the AUTO_PUBLISHING workflow

                              |  N/PUBLISHED   | PUBLISHED
            ----------------------------------------------
                N/APPROVED    |     GM/OWR     |     -
                APPROVED      |   registerd    |    all
            ----------------------------------------------
          - There are few exceptions accordingly to the enabled workflow
            * SIMPLIFIED WORKFLOW: If the resource will be "approved" or "published" the OWNERS won't be able change the resource data and perms
            * ADVANCED WORKFLOW: If the resource will be "approved" or "published" the OWNERS won't be able change the resource data, metadata and perms
        """
        _resource = instance or AdvancedSecurityWorkflowManager.get_instance(uuid)
        _perm_spec = copy.deepcopy(perm_spec)

        def safe_remove(perms, perm): perms.remove(perm) if perm in perms else None

        if _resource:
            _resource = _resource.get_real_instance()

            AdminViewPermissionsSet = AdvancedSecurityWorkflowManager.compute_admin_and_view_permissions_set(uuid, instance=_resource)
            ResourceGroupsAndMembersSet = AdvancedSecurityWorkflowManager.compute_resource_groups_and_members_set(uuid, instance=_resource, group=_resource.group)

            # Computing the OWNER Permissions
            prev_perms = _perm_spec['users'].get(_resource.owner, []) if isinstance(_perm_spec['users'], dict) else []
            prev_perms += AdminViewPermissionsSet.view_perms.copy() + AdminViewPermissionsSet.admin_perms.copy()
            prev_perms = list(set(prev_perms))
            if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow():
                # Check if owner is a manager of any group and add admin_manager_perms accordingly
                if _resource.owner not in ResourceGroupsAndMembersSet.managers:
                    safe_remove(prev_perms, 'publish_resourcebase')
                    if not AdvancedSecurityWorkflowManager.is_simple_publishing_workflow() and (_resource.is_approved or _resource.is_published):
                        safe_remove(prev_perms, 'change_resourcebase')
                        safe_remove(prev_perms, 'change_resourcebase_metadata')
                        safe_remove(prev_perms, 'delete_resourcebase')
                        if _resource.polymorphic_ctype.model == "layer":
                            safe_remove(prev_perms, 'change_layer_style')
                            safe_remove(prev_perms, 'change_layer_data')
                    if AdvancedSecurityWorkflowManager.is_advanced_workflow():
                        safe_remove(prev_perms, 'change_resourcebase_permissions')
            _perm_spec['users'][_resource.owner] = list(set(prev_perms))

            # Computing the MANAGERs and MEMBERs Permissions
            if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow():
                if group_status_changed:
                    # Reset Groups/Manager Perms
                    _owner_perms = copy.deepcopy(_perm_spec['users'].get(_resource.owner, []))
                    _perm_spec['users'] = {_resource.owner: _owner_perms}
                    _perm_spec['groups'] = {}

                if ResourceGroupsAndMembersSet.managers:
                    for user in ResourceGroupsAndMembersSet.managers:
                        prev_perms = _perm_spec["users"].get(user, []) if "users" in _perm_spec else []
                        prev_perms += AdminViewPermissionsSet.view_perms.copy() + AdminViewPermissionsSet.admin_perms.copy()
                        prev_perms = list(set(prev_perms))
                        _perm_spec["users"][user] = list(set(prev_perms))

                if ResourceGroupsAndMembersSet.resource_groups:
                    for group in ResourceGroupsAndMembersSet.resource_groups:
                        prev_perms = _perm_spec["groups"].get(group, []) if "groups" in _perm_spec else []
                        prev_perms += AdminViewPermissionsSet.view_perms.copy()
                        prev_perms = list(set(prev_perms))
                        _perm_spec["groups"][group] = list(set(prev_perms))
                elif len(_perm_spec["groups"]):
                    groups = copy.deepcopy(_perm_spec["groups"])
                    for group in groups:
                        if group not in (ResourceGroupsAndMembersSet.anonymous_group, ResourceGroupsAndMembersSet.registered_members_group):
                            try:
                                group = group if hasattr(group, 'group') else GroupProfile.objects.get(group=group)
                                users = list(group.get_managers()) + list(group.get_members())
                                for user in users:
                                    if _perm_spec["users"].get(user, None):
                                        _perm_spec["users"].pop(user)
                                if _perm_spec["groups"].get(group.group, None):
                                    _perm_spec["groups"].pop(group.group)
                            except Exception as e:
                                logger.exception(e)

            # Computing the 'All Others' Permissions
            if ResourceGroupsAndMembersSet.anonymous_group:
                prev_perms = _perm_spec['groups'].get(ResourceGroupsAndMembersSet.anonymous_group, []) if isinstance(_perm_spec['groups'], dict) else []
                if approval_status_changed and (_resource.is_approved or _resource.is_published):
                    prev_perms += AdminViewPermissionsSet.view_perms.copy()
                    prev_perms = list(set(prev_perms))
                if created:
                    if not AdvancedSecurityWorkflowManager.is_anonymous_can_view():
                        safe_remove(prev_perms, 'view_resourcebase')
                    if not AdvancedSecurityWorkflowManager.is_anonymous_can_download():
                        safe_remove(prev_perms, 'download_resourcebase')
                if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow():
                    if ((AdvancedSecurityWorkflowManager.is_simple_publishing_workflow() or AdvancedSecurityWorkflowManager.is_advanced_workflow()) and not _resource.is_published) or (
                            AdvancedSecurityWorkflowManager.is_simplified_workflow() and not (_resource.is_approved or _resource.is_published)):
                        safe_remove(prev_perms, 'view_resourcebase')
                        safe_remove(prev_perms, 'download_resourcebase')
            _perm_spec['groups'][ResourceGroupsAndMembersSet.anonymous_group] = list(set(prev_perms))

            if ResourceGroupsAndMembersSet.registered_members_group and getattr(groups_settings, 'AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME', False):
                prev_perms = _perm_spec['groups'].get(ResourceGroupsAndMembersSet.registered_members_group, []) if isinstance(_perm_spec['groups'], dict) else []
                if approval_status_changed and (_resource.is_approved or _resource.is_published):
                    prev_perms += AdminViewPermissionsSet.view_perms.copy()
                    prev_perms = list(set(prev_perms))
                if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow() and not _resource.is_approved:
                    safe_remove(prev_perms, 'view_resourcebase')
                    safe_remove(prev_perms, 'download_resourcebase')
                _perm_spec['groups'][ResourceGroupsAndMembersSet.registered_members_group] = list(set(prev_perms))

        return _perm_spec

    @staticmethod
    def get_permissions(uuid: str, /, instance=None, permissions: dict = {}, created: bool = False,
                        approval_status_changed: bool = False, group_status_changed: bool = False) -> dict:
        """
          Fix-ups the perm_spec accordingly to the enabled workflow (if any).
          For more details check the "get_workflow_permissions" method
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
            perm_spec = AdvancedSecurityWorkflowManager.get_workflow_permissions(
                _resource.uuid, instance=_resource, perm_spec=perm_spec, created=created,
                approval_status_changed=approval_status_changed, group_status_changed=group_status_changed)

        return perm_spec

    @staticmethod
    def handle_moderated_uploads(uuid: str, /, instance=None) -> object:
        _resource = instance or AdvancedSecurityWorkflowManager.get_instance(uuid)

        if _resource:
            if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow():
                _resource.is_approved = False
                _resource.was_approved = False
                _resource.is_published = False
                _resource.was_published = False

                from geonode.base.models import ResourceBase
                ResourceBase.objects.filter(
                    uuid=_resource.uuid).update(
                        is_approved=False, was_approved=False,
                        is_published=False, was_published=False)

        return _resource

    @staticmethod
    def set_group_member_permissions(user, group, role):

        if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow():
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
            )
            _resources = set([_r for _r in queryset.iterator()])
            if len(_resources) == 0:
                queryset = (
                    get_objects_for_user(
                        user,
                        ["base.view_resourcebase", "base.change_resourcebase"],
                        any_perm=True)
                    .filter(owner=user)
                )
                _resources = queryset.iterator()
            for _r in _resources:
                perm_spec = _r.get_all_level_info()
                if "users" not in perm_spec:
                    perm_spec["users"] = {}
                if "groups" not in perm_spec:
                    perm_spec["groups"] = {}

                AdminViewPermissionsSet = AdvancedSecurityWorkflowManager.compute_admin_and_view_permissions_set(_r.uuid, instance=_r)

                prev_perms = AdminViewPermissionsSet.view_perms.copy()
                if not role:
                    prev_perms = []
                    if user == _r.owner:
                        _group = group if hasattr(group, 'group') else GroupProfile.objects.get(group=group)
                        _users = list(_group.get_managers()) + list(_group.get_members())
                        for _m in _users:
                            if perm_spec["users"].get(_m, None):
                                perm_spec["users"].pop(_m)

                        if perm_spec["groups"].get(_group.group, None):
                            perm_spec["groups"].pop(_group.group)
                elif role == "manager":
                    prev_perms += AdminViewPermissionsSet.admin_perms.copy()
                    prev_perms = list(set(prev_perms))
                perm_spec["users"][user] = list(set(prev_perms))

                # Let's the ResourceManager finally decide which are the correct security settings to apply
                _r.set_permissions(perm_spec)


class ResourceManager:

    @staticmethod
    def remove_permissions(uuid: str, /, instance=None) -> bool:
        """Remove object permissions on given resource.
        If is a layer removes the layer specific permissions then the
        resourcebase permissions.
        """
        _resource = instance or AdvancedSecurityWorkflowManager.get_instance(uuid)
        if _resource:
            try:
                with transaction.atomic():
                    logger.debug(f'Removing all permissions on {_resource}')
                    from geonode.layers.models import Layer
                    _layer = _resource.get_real_instance() if isinstance(_resource.get_real_instance(), Layer) else None
                    if not _layer:
                        try:
                            _layer = _resource.layer if hasattr(_resource, "layer") else None
                        except Exception:
                            _layer = None
                    if _layer:
                        UserObjectPermission.objects.filter(
                            content_type=ContentType.objects.get_for_model(_layer),
                            object_pk=_resource.id
                        ).delete()
                        GroupObjectPermission.objects.filter(
                            content_type=ContentType.objects.get_for_model(_layer),
                            object_pk=_resource.id
                        ).delete()
                    UserObjectPermission.objects.filter(
                        content_type=ContentType.objects.get_for_model(_resource.get_self_resource()),
                        object_pk=_resource.id).delete()
                    GroupObjectPermission.objects.filter(
                        content_type=ContentType.objects.get_for_model(_resource.get_self_resource()),
                        object_pk=_resource.id).delete()
                    if not gs_security.remove_permissions(instance=_resource):
                        raise Exception("Could not set the GeoServer rules successfully!")
                return True
            except Exception as e:
                logger.exception(e)
                _resource.set_processing_state("FAILED")
        return False

    @staticmethod
    def set_permissions(uuid: str, /, instance=None, owner: settings.AUTH_USER_MODEL = None, permissions: dict = {}, created: bool = False,
                        approval_status_changed: bool = False, group_status_changed: bool = False) -> bool:
        from geonode.base.models import ResourceBase

        _resource = instance or AdvancedSecurityWorkflowManager.get_instance(uuid)
        if _resource:
            _resource = _resource.get_real_instance()
            logger.debug(f'Finalizing (permissions and notifications) on resource {instance}')
            try:
                with transaction.atomic():
                    logger.debug(f'Setting permissions {permissions} on {_resource}')

                    # default permissions for owner
                    if owner and owner != _resource.owner:
                        _resource.owner = owner
                        ResourceBase.objects.filter(uuid=_resource.uuid).update(owner=owner)
                    _owner = _resource.owner
                    _resource_type = _resource.resource_type or _resource.polymorphic_ctype.name

                    # default permissions for anonymous users
                    anonymous_group, _ = Group.objects.get_or_create(name='anonymous')

                    if not anonymous_group:
                        raise Exception("Could not acquire 'anonymous' Group.")

                    # Gathering and validating the current permissions (if any has been passed)
                    if not created and permissions is None:
                        permissions = _resource.get_all_level_info()

                    if permissions:
                        if PermSpecCompact.validate(permissions):
                            _permissions = PermSpecCompact(copy.deepcopy(permissions), _resource).extended
                        else:
                            _permissions = copy.deepcopy(permissions)
                    else:
                        _permissions = None

                    # Fixup Advanced Workflow permissions
                    _perm_spec = AdvancedSecurityWorkflowManager.get_permissions(
                        _resource.uuid, instance=_resource, permissions=_permissions, created=created,
                        approval_status_changed=approval_status_changed, group_status_changed=group_status_changed)

                    """
                    Cleanup the Guardian tables
                    """
                    ResourceManager.remove_permissions(uuid, instance=_resource)

                    if permissions is not None and len(permissions):
                        """
                        Sets an object's the permission levels based on the perm_spec JSON.

                        the mapping looks like:
                        {
                            'users': {
                                'AnonymousUser': ['view'],
                                <username>: ['perm1','perm2','perm3'],
                                <username2>: ['perm1','perm2','perm3']
                                ...
                            },
                            'groups': [
                                <groupname>: ['perm1','perm2','perm3'],
                                <groupname2>: ['perm1','perm2','perm3'],
                                ...
                            ]
                        }
                        """
                        # Anonymous User group
                        if 'users' in _perm_spec and ("AnonymousUser" in _perm_spec['users'] or get_anonymous_user() in _perm_spec['users']):
                            anonymous_user = "AnonymousUser" if "AnonymousUser" in _perm_spec['users'] else get_anonymous_user()
                            perms = copy.deepcopy(_perm_spec['users'][anonymous_user])
                            _perm_spec['users'].pop(anonymous_user)
                            _prev_perm = _perm_spec["groups"].get(anonymous_group, []) if "groups" in _perm_spec else []
                            _perm_spec["groups"][anonymous_group] = set.union(perms_as_set(_prev_perm), perms_as_set(perms))
                            for perm in _perm_spec["groups"][anonymous_group]:
                                if _resource_type == 'layer' and perm in (
                                        'change_layer_data', 'change_layer_style',
                                        'add_layer', 'change_layer', 'delete_layer'):
                                    try:
                                        assign_perm(perm, anonymous_group, _resource.layer)
                                    except Permission.DoesNotExist as e:
                                        logger.exception(e)
                                        logger.exception(f"Permissions {perm} does not exists for resource {_resource.layer}")
                                elif AdvancedSecurityWorkflowManager.assignable_perm_condition(perm, _resource_type):
                                    try:
                                        assign_perm(perm, anonymous_group, _resource.get_self_resource())
                                    except Permission.DoesNotExist as e:
                                        logger.exception(e)
                                        logger.exception(f"Permissions {perm} does not exists for resource {_resource.get_self_resource()}")

                        # All the other users
                        if 'users' in _perm_spec and len(_perm_spec['users']) > 0:
                            for user, perms in _perm_spec['users'].items():
                                _user = get_user_model().objects.get(username=user)
                                if user != "AnonymousUser" and user != get_anonymous_user():
                                    for perm in perms:
                                        if _resource_type == 'layer' and perm in (
                                                'change_layer_data', 'change_layer_style',
                                                'add_layer', 'change_layer', 'delete_layer'):
                                            try:
                                                assign_perm(perm, _user, _resource.layer)
                                            except Permission.DoesNotExist as e:
                                                logger.exception(e)
                                                logger.exception(f"Permissions {perm} does not exists for resource {_resource.layer}")
                                        elif AdvancedSecurityWorkflowManager.assignable_perm_condition(perm, _resource_type):
                                            try:
                                                assign_perm(perm, _user, _resource.get_self_resource())
                                            except Permission.DoesNotExist as e:
                                                logger.exception(e)
                                                logger.exception(f"Permissions {perm} does not exists for resource {_resource}")

                        # All the other groups
                        if 'groups' in _perm_spec and len(_perm_spec['groups']) > 0:
                            for group, perms in _perm_spec['groups'].items():
                                _group = Group.objects.get(name=group)
                                for perm in perms:
                                    if _resource_type == 'layer' and perm in (
                                            'change_layer_data', 'change_layer_style',
                                            'add_layer', 'change_layer', 'delete_layer'):
                                        try:
                                            assign_perm(perm, _group, _resource.layer)
                                        except Permission.DoesNotExist as e:
                                            logger.exception(e)
                                            logger.exception(f"Permissions {perm} does not exists for resource {_resource.layer}")
                                    elif AdvancedSecurityWorkflowManager.assignable_perm_condition(perm, _resource_type):
                                        try:
                                            assign_perm(perm, _group, _resource.get_self_resource())
                                        except Permission.DoesNotExist as e:
                                            logger.exception(e)
                                            logger.exception(f"Permissions {perm} does not exists for resource {_resource.get_self_resource()}")
                    else:
                        # Anonymous
                        if AdvancedSecurityWorkflowManager.is_anonymous_can_view():
                            assign_perm('view_resourcebase', anonymous_group, _resource.get_self_resource())
                            _prev_perm = _perm_spec["groups"].get(anonymous_group, []) if "groups" in _perm_spec else []
                            _perm_spec["groups"][anonymous_group] = set.union(perms_as_set(_prev_perm), perms_as_set('view_resourcebase'))
                        else:
                            for user_group in get_user_groups(_owner):
                                if not skip_registered_members_common_group(user_group):
                                    assign_perm('view_resourcebase', user_group, _resource.get_self_resource())
                                    _prev_perm = _perm_spec["groups"].get(user_group, []) if "groups" in _perm_spec else []
                                    _perm_spec["groups"][user_group] = set.union(perms_as_set(_prev_perm), perms_as_set('view_resourcebase'))

                        if AdvancedSecurityWorkflowManager.assignable_perm_condition('download_resourcebase', _resource_type):
                            if AdvancedSecurityWorkflowManager.is_anonymous_can_download():
                                assign_perm('download_resourcebase', anonymous_group, _resource.get_self_resource())
                                _prev_perm = _perm_spec["groups"].get(anonymous_group, []) if "groups" in _perm_spec else []
                                _perm_spec["groups"][anonymous_group] = set.union(perms_as_set(_prev_perm), perms_as_set('download_resourcebase'))
                            else:
                                for user_group in get_user_groups(_owner):
                                    if not skip_registered_members_common_group(user_group):
                                        assign_perm('download_resourcebase', user_group, _resource.get_self_resource())
                                        _prev_perm = _perm_spec["groups"].get(user_group, []) if "groups" in _perm_spec else []
                                        _perm_spec["groups"][user_group] = set.union(perms_as_set(_prev_perm), perms_as_set('download_resourcebase'))

                        if _resource.__class__.__name__ == 'Layer':
                            # only for layer owner
                            assign_perm('change_layer_data', _owner, _resource)
                            assign_perm('change_layer_style', _owner, _resource)
                            _prev_perm = _perm_spec["users"].get(_owner, []) if "users" in _perm_spec else []
                            _perm_spec["users"][_owner] = set.union(perms_as_set(_prev_perm), perms_as_set(['change_layer_data', 'change_layer_style']))

                        _resource = AdvancedSecurityWorkflowManager.handle_moderated_uploads(_resource.uuid, instance=_resource)

                    # Fixup GIS Backend Security Rules Accordingly
                    if not gs_security.set_permissions(
                            instance=_resource, owner=owner, permissions=_perm_spec, created=created):
                        # This might not be a severe error. E.g. for layers outside of local GeoServer
                        logger.error(Exception("Could not complete concrete manager operation successfully!"))
                return True
            except Exception as e:
                logger.exception(e)
                _resource.set_processing_state("FAILED")
        return False
