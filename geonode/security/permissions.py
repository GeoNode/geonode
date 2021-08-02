#########################################################################
#
# Copyright (C) 2021 OSGeo
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
import json
import pprint
import collections

from guardian.shortcuts import get_anonymous_user
from avatar.templatetags.avatar_tags import avatar_url

from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from geonode.groups.conf import settings as groups_settings

# Permissions mapping
PERMISSIONS = {
    'add_resourcebase': 'add_resource',
}

# The following permissions will be filtered out when READ_ONLY mode is active
READ_ONLY_AFFECTED_PERMISSIONS = [
    'add_resource',
]

# Permissions on resources
VIEW_PERMISSIONS = [
    'view_resourcebase',
]

DOWNLOAD_PERMISSIONS = [
    'download_resourcebase',
]

EDIT_PERMISSIONS = [
    'change_resourcebase',
]

MANAGE_PERMISSIONS = [
    'change_resourcebase_metadata',
    'delete_resourcebase',
    'change_resourcebase_permissions',
    'publish_resourcebase',
]

ADMIN_PERMISSIONS = MANAGE_PERMISSIONS + EDIT_PERMISSIONS

DATASET_ADMIN_PERMISSIONS = [
    'change_dataset_data',
    'change_dataset_style'
]

SERVICE_PERMISSIONS = [
    "add_service",
    "delete_service",
    "change_resourcebase_metadata",
    "add_resourcebase_from_service"
]

VIEW_RIGHTS = "view"
DOWNLOAD_RIGHTS = "download"
EDIT_RIGHTS = "edit"
MANAGE_RIGHTS = "manage"

COMPACT_RIGHT_MODES = (
    (VIEW_RIGHTS, "view"),
    (DOWNLOAD_RIGHTS, "download"),
    (EDIT_RIGHTS, "edit"),
    (MANAGE_RIGHTS, "manage"),
)


def _to_extended_perms(perm: str, resource_type: str = None) -> list:
    """Collects standard permissions into a "compact" set, accordingly to the schema below:

      - view: view resource
      - download: view and download
      - edit: view download and edit (metadata, style, data)
      - manage: change permissions, delete resource, etc.

    """
    if perm is None or len(perm) == 0:
        return []
    if perm == VIEW_RIGHTS:
        return VIEW_PERMISSIONS
    if perm == DOWNLOAD_RIGHTS:
        return VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS
    if perm == EDIT_RIGHTS:
        if resource_type and resource_type.lower() in 'dataset':
            return DATASET_ADMIN_PERMISSIONS + EDIT_PERMISSIONS
        else:
            return EDIT_PERMISSIONS
    if perm == MANAGE_RIGHTS:
        return MANAGE_PERMISSIONS


def _to_compact_perms(perms: list, resource_type: str = None) -> str:
    """Collects standard permissions into a "compact" set, accordingly to the schema below:

      - view: view resource
      - download: view and download
      - edit: view download and edit (metadata, style, data)
      - manage: change permissions, delete resource, etc.

    """
    if perms is None or len(perms) == 0:
        return None
    if any(_p in MANAGE_PERMISSIONS for _p in perms):
        return MANAGE_RIGHTS
    elif resource_type and resource_type.lower() in 'dataset' and any(_p in DATASET_ADMIN_PERMISSIONS + EDIT_PERMISSIONS for _p in perms):
        return EDIT_RIGHTS
    elif any(_p in DATASET_ADMIN_PERMISSIONS + EDIT_PERMISSIONS for _p in perms):
        return EDIT_RIGHTS
    elif any(_p in DOWNLOAD_PERMISSIONS for _p in perms):
        return DOWNLOAD_RIGHTS
    elif any(_p in VIEW_PERMISSIONS for _p in perms):
        return VIEW_RIGHTS
    return None


_Binding = collections.namedtuple('Binding', [
    'name', 'expected', 'ro', 'binding'
])

_User = collections.namedtuple('User', [
    'id', 'username', 'last_name', 'first_name', 'avatar'
])

_Group = collections.namedtuple('User', [
    'id', 'title', 'name'
])


def _binding(name, expected=True, ro=True, binding=None):
    return _Binding(name, expected, ro, binding)


class BindingFailed(Exception):
    '''Something in the API has changed'''
    pass


class PermSpecConverterBase(object):

    _object_name = None

    def __init__(self, json, resource_type=None, parent=None):
        self._resource_type = resource_type
        self._parent = parent
        if parent == self:
            raise Exception('bogus')
        if json is not None:
            self._bind_json(json)

    def _bind_json(self, json):
        # generally, not required for override. instead use _bind_custom_json
        # if possible
        if not isinstance(json, dict):
            self._binding_failed('expected dict, got %s', type(json))
        for binding in self._bindings:
            val = json.pop(binding.name, None)
            if binding.expected and val is None:
                self._binding_failed('expected val for %s', binding.name)
            if binding.binding and val is not None:
                if isinstance(val, list):
                    val = [binding.binding(v, parent=self) for v in val]
                else:
                    val = binding.binding(val, parent=self)
            setattr(self, binding.name, val)
        self._bind_custom_json(json)

    def _bind_custom_json(self, json):
        # do any custom binding like for a shortcut
        pass

    def _binding_failed(self, msg, args):
        raise BindingFailed(f'[{type(self)}] {msg % args}')

    def _to_json_object(self, deep=True, top_level=True):
        _json = {}
        for binding in self._bindings:
            val = getattr(self, binding.name, None)
            if isinstance(val, PermSpecConverterBase):
                val = val._to_json_object(top_level=False)
            if val is not None:
                _json[binding.name] = val
        self._to_json_object_custom(_json)
        if top_level and self._object_name:
            _json = {self._object_name: _json}
        return _json.copy()

    def _to_json_object_custom(self, json):
        pass

    def __repr__(self):
        _json = self._to_json_object(deep=True, top_level=False)
        try:
            return json.dumps(_json)
        except Exception:
            return pprint.pformat(_json, indent=2)


class PermSpec(PermSpecConverterBase):

    _object_name = 'perm_spec'
    _bindings = (
        _binding('users'),
        _binding('groups'),
    )

    @property
    def compact(self):
        """Converts a standard and verbose 'perm_spec' into 'compact mode'.

         - The method also recognizes special/internal security groups, like 'anonymous' and 'registered-members' and places
           their permissions on a specific node called 'groups'.
         - Every security group, different from the former ones, associated to a GeoNode 'GroupProfile', will be placed on a
           node called 'organizations' instead.
        e.g.:

        ```
        {
            "users": [
                {
                    "id": 1001,
                    "username": "afabiani",
                    "first_name": "",
                    "last_name": "",
                    "avatar": "",
                    "permissions": "manage"
                }
            ],
            "organizations": [],
            "groups": [
                {
                    "id": 3,
                    "title": "Registered Members",
                    "name": "registered-members",
                    "permissions": "edit"
                },
                {
                    "id": 2,
                    "title": "anonymous",
                    "name": "anonymous",
                    "permissions": "download"
                }
            ]
        }
        ```
        """
        from geonode.base.utils import build_absolute_uri

        json = {}
        user_perms = []
        group_perms = []
        anonymous_perms = None
        organization_perms = []

        for _k in self.users:
            _perms = self.users[_k]
            if isinstance(_k, str):
                _k = get_user_model().objects.get(username=_k)
            if not _k.is_anonymous and _k.username != 'AnonymousUser':
                avatar = build_absolute_uri(avatar_url(_k, 240))
                user = _User(_k.id, _k.username, _k.last_name, _k.first_name, avatar)
                user_perms.append(
                    {
                        'id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'avatar': user.avatar,
                        'permissions': _to_compact_perms(_perms)
                    }
                )
            else:
                anonymous_perms = {
                    'id': Group.objects.get(name='anonymous').id,
                    'title': 'anonymous',
                    'name': 'anonymous',
                    'permissions': _to_compact_perms(_perms)
                }

        for _k in self.groups:
            _perms = self.groups[_k]
            if isinstance(_k, str):
                _k = Group.objects.get(name=_k)
            if _k.name == 'anonymous':
                anonymous_perms = {
                    'id': _k.id,
                    'title': 'anonymous',
                    'name': 'anonymous',
                    'permissions': _to_compact_perms(_perms)
                }
            elif hasattr(_k, 'groupprofile'):
                group = _Group(_k.id, _k.groupprofile.title, _k.name)
                if _k.name == groups_settings.REGISTERED_MEMBERS_GROUP_NAME:
                    group_perms.append(
                        {
                            'id': group.id,
                            'title': group.title,
                            'name': group.name,
                            'permissions': _to_compact_perms(_perms)
                        }
                    )
                else:
                    organization_perms.append(
                        {
                            'id': group.id,
                            'title': group.title,
                            'name': group.name,
                            'permissions': _to_compact_perms(_perms)
                        }
                    )

        if anonymous_perms:
            group_perms.append(anonymous_perms)
        json['users'] = user_perms
        json['organizations'] = organization_perms
        json['groups'] = group_perms
        return json.copy()


class PermSpecUserCompact(PermSpecConverterBase):

    _object_name = 'perm_spec_user_compact'
    _bindings = (
        _binding('id'),
        _binding('username'),
        _binding('first_name'),
        _binding('last_name'),
        _binding('avatar'),
        _binding('permissions'),
    )


class PermSpecGroupCompact(PermSpecConverterBase):

    _object_name = 'perm_spec_group_compact'
    _bindings = (
        _binding('id'),
        _binding('title'),
        _binding('name'),
        _binding('permissions'),
    )


class PermSpecCompact(PermSpecConverterBase):

    _object_name = 'perm_spec_compact'
    _bindings = (
        _binding('users', expected=False, binding=PermSpecUserCompact),
        _binding('organizations', expected=False, binding=PermSpecGroupCompact),
        _binding('groups', expected=False, binding=PermSpecGroupCompact),
    )

    @property
    def extended(self):
        """Converts a 'perm_spec' in 'compact mode' into standard and verbose one.

        e.g.:

        ```
        {
            'groups': {
                <Group: registered-members>: ['view_resourcebase',
                                             'download_resourcebase',
                                             'change_resourcebase'],
                <Group: anonymous>: ['view_resourcebase']
            },
            'users': {
                <Profile: AnonymousUser>: ['view_resourcebase'],
                <Profile: afabiani>: ['view_resourcebase',
                                    'download_resourcebase',
                                    'change_resourcebase_metadata',
                                    'change_resourcebase',
                                    'delete_resourcebase',
                                    'change_resourcebase_permissions',
                                    'publish_resourcebase']
            }
        }
        ```
        """
        json = {
            'users': {},
            'groups': {}
        }
        for _u in self.users:
            _user_profile = get_user_model().objects.get(id=_u.id)
            json['users'][_user_profile.username] = _to_extended_perms(_u.permissions, self._resource_type)
        for _go in self.organizations:
            _group = Group.objects.get(id=_go.id)
            json['groups'][_group.name] = _to_extended_perms(_go.permissions, self._resource_type)
        for _go in self.groups:
            _group = Group.objects.get(id=_go.id)
            json['groups'][_group.name] = _to_extended_perms(_go.permissions, self._resource_type)
            if _go.name == 'anonymous':
                _user_profile = get_anonymous_user()
                json['users'][_user_profile.username] = _to_extended_perms(_go.permissions, self._resource_type)
        return json.copy()

    def merge(self, perm_spec_compact_patch: "PermSpecCompact"):
        """Merges 'perm_spec_compact_patch' to the current one.

         - Existing elements will be overridden.
         - Non existing elements will be added.
         - If you need to delete elements you cannot use this method.
        """
        for _elem in ('users', 'groups', 'organizations'):
            for _up in getattr(perm_spec_compact_patch, _elem, []) or []:
                _merged = False
                for _i, _u in enumerate(getattr(self, _elem, []) or []):
                    if _up.id == _u.id:
                        getattr(self, _elem)[_i] = _up
                        getattr(self, _elem)[_i].parent = self
                        _merged = True
                        break
                if not _merged:
                    if isinstance(getattr(self, _elem), list):
                        getattr(self, _elem).append(_up)
                    else:
                        getattr(self, _elem).add(_up)
