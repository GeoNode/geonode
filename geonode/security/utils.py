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
import logging
from itertools import chain

from django.apps import apps
from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission
from guardian.utils import get_user_obj_perms_model
from guardian.shortcuts import (
    assign_perm,
    get_objects_for_user)

from geonode.groups.models import GroupProfile
from geonode.groups.conf import settings as groups_settings
from geonode.security.permissions import DATASET_EDIT_DATA_PERMISSIONS

logger = logging.getLogger(__name__)


def get_visible_resources(queryset,
                          user,
                          request=None,
                          metadata_only=False,
                          admin_approval_required=False,
                          unpublished_not_visible=False,
                          private_groups_not_visibile=False):
    # Get the list of objects the user has access to
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


def set_owner_permissions(resource, members=None):
    """assign all admin permissions to the owner"""
    from .permissions import (
        VIEW_PERMISSIONS,
        DOWNLOAD_PERMISSIONS,
        ADMIN_PERMISSIONS,
        SERVICE_PERMISSIONS,
        DOWNLOADABLE_RESOURCES,
        DATASET_ADMIN_PERMISSIONS,
        DATASET_EDIT_STYLE_PERMISSIONS)
    _perm_spec = {
        "users": {},
        "groups": {}
    }
    if resource.polymorphic_ctype:
        # Owner & Manager Admin Perms
        admin_perms = VIEW_PERMISSIONS + ADMIN_PERMISSIONS
        if resource.polymorphic_ctype.name in DOWNLOADABLE_RESOURCES:
            admin_perms += DOWNLOAD_PERMISSIONS
        for perm in admin_perms:
            if not settings.RESOURCE_PUBLISHING and not settings.ADMIN_MODERATE_UPLOADS:
                assign_perm(perm, resource.owner, resource.get_self_resource())
                _prev_perm = _perm_spec["users"].get(resource.owner, []) if "users" in _perm_spec else []
                _perm_spec["users"][resource.owner] = set.union(perms_as_set(_prev_perm), perms_as_set(perm))
            elif perm not in {'change_resourcebase_permissions', 'publish_resourcebase'}:
                assign_perm(perm, resource.owner, resource.get_self_resource())
                _prev_perm = _perm_spec["users"].get(resource.owner, []) if "users" in _perm_spec else []
                _perm_spec["users"][resource.owner] = set.union(perms_as_set(_prev_perm), perms_as_set(perm))
            if members:
                for user in members:
                    assign_perm(perm, user, resource.get_self_resource())
                    _prev_perm = _perm_spec["users"].get(user, []) if "users" in _perm_spec else []
                    _perm_spec["users"][user] = set.union(perms_as_set(_prev_perm), perms_as_set(perm))

        # Set the GeoFence Owner Rule
        if resource.polymorphic_ctype.name == 'dataset':
            DATA_EDIT_PERMISSIONS = []
            if resource.get_real_instance().subtype == 'vector':
                DATA_EDIT_PERMISSIONS = DATASET_ADMIN_PERMISSIONS
            elif resource.get_real_instance().subtype == 'raster':
                DATA_EDIT_PERMISSIONS = DATASET_EDIT_STYLE_PERMISSIONS
            for perm in DATA_EDIT_PERMISSIONS:
                assign_perm(perm, resource.owner, resource.dataset)
                _prev_perm = _perm_spec["users"].get(resource.owner, []) if "users" in _perm_spec else []
                _perm_spec["users"][resource.owner] = set.union(perms_as_set(_prev_perm), perms_as_set(perm))
                if members:
                    for user in members:
                        assign_perm(perm, user, resource.dataset)
                        _prev_perm = _perm_spec["users"].get(user, []) if "users" in _perm_spec else []
                        _perm_spec["users"][user] = set.union(perms_as_set(_prev_perm), perms_as_set(perm))

        if resource.polymorphic_ctype.name == 'service':
            for perm in SERVICE_PERMISSIONS:
                assign_perm(perm, resource.owner, resource.service)
                _prev_perm = _perm_spec["users"].get(resource.owner, []) if "users" in _perm_spec else []
                _perm_spec["users"][resource.owner] = set.union(perms_as_set(_prev_perm), perms_as_set(perm))
                if members:
                    for user in members:
                        assign_perm(perm, user, resource.service)
                        _prev_perm = _perm_spec["users"].get(user, []) if "users" in _perm_spec else []
                        _perm_spec["users"][user] = set.union(perms_as_set(_prev_perm), perms_as_set(perm))
    return _perm_spec


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


def get_obj_group_managers(owner):
    """
    Returns the managers of all the groups belonging to the "owner"
    """
    obj_group_managers = []
    if get_user_groups(owner):
        for _user_group in get_user_groups(owner):
            if not skip_registered_members_common_group(Group.objects.get(name=_user_group)):
                try:
                    _group_profile = GroupProfile.objects.get(slug=_user_group)
                    managers = _group_profile.get_managers()
                    if managers:
                        for manager in managers:
                            if manager not in obj_group_managers and not manager.is_superuser:
                                obj_group_managers.append(manager)
                except GroupProfile.DoesNotExist as e:
                    logger.exception(e)
    return obj_group_managers
