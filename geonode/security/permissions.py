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
import jsonschema
import collections

from avatar.templatetags.avatar_tags import avatar_url
from guardian.shortcuts import get_group_perms, get_anonymous_user

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from geonode.utils import build_absolute_uri
from geonode.groups.conf import settings as groups_settings


# Permissions mapping
PERMISSIONS = {
    'add_resourcebase': 'add_resource',
}

DOWNLOADABLE_RESOURCES = [
    'layer',
    'document'
]

DATA_EDITABLE_RESOURCES_SUBTYPES = [
    'dataStore'
]

DATA_STYLABLE_RESOURCES_SUBTYPES = [
    'coverageStore',
    'dataStore'
]

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

BASIC_MANAGE_PERMISSIONS = [
    'change_resourcebase_metadata',
    'delete_resourcebase',
]

MANAGE_PERMISSIONS = BASIC_MANAGE_PERMISSIONS + [
    'change_resourcebase_permissions',
    'publish_resourcebase',
]

ADMIN_PERMISSIONS = MANAGE_PERMISSIONS + EDIT_PERMISSIONS

OWNER_PERMISSIONS = ADMIN_PERMISSIONS + VIEW_PERMISSIONS

LAYER_EDIT_DATA_PERMISSIONS = ['change_layer_data', ]
LAYER_EDIT_STYLE_PERMISSIONS = ['change_layer_style', ]
LAYER_ADMIN_PERMISSIONS = LAYER_EDIT_DATA_PERMISSIONS + LAYER_EDIT_STYLE_PERMISSIONS

SERVICE_PERMISSIONS = [
    "add_service",
    "delete_service",
    "change_resourcebase_metadata",
    "add_resourcebase_from_service"
]

DEFAULT_PERMISSIONS = []
if settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION:
    DEFAULT_PERMISSIONS += VIEW_PERMISSIONS
if settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION:
    DEFAULT_PERMISSIONS += DOWNLOAD_PERMISSIONS

DEFAULT_PERMS_SPEC = json.dumps({"users": {"AnonymousUser": DEFAULT_PERMISSIONS}, "groups": {}})

NONE_RIGHTS = "none"
VIEW_RIGHTS = "view"
DOWNLOAD_RIGHTS = "download"
EDIT_RIGHTS = "edit"
MANAGE_RIGHTS = "manage"
OWNER_RIGHTS = "owner"

COMPACT_RIGHT_MODES = (
    (VIEW_RIGHTS, "view"),
    (DOWNLOAD_RIGHTS, "download"),
    (EDIT_RIGHTS, "edit"),
    (MANAGE_RIGHTS, "manage"),
    (OWNER_RIGHTS, "owner"),
)


PERM_SPEC_COMPACT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "users": {
            "type": "array",
            "items": [
                {
                    "type": "object",
                    "properties": {
                        "avatar": {
                            "type": "string"
                        },
                        "first_name": {
                            "type": "string"
                        },
                        "id": {
                            "type": "integer"
                        },
                        "last_name": {
                            "type": "string"
                        },
                        "permissions": {
                            "type": "string",
                            "enum": ["none", "view", "download", "edit", "manage", "owner"]
                        },
                        "username": {
                            "type": "string"
                        },
                        "is_staff": {
                            "type": "boolean"
                        },
                        "is_superuser": {
                            "type": "boolean"
                        }
                    },
                    "required": [
                        "avatar",
                        "first_name",
                        "id",
                        "last_name",
                        "permissions",
                        "username",
                        "is_staff",
                        "is_superuser"
                    ]
                }
            ]
        },
        "organizations": {
            "type": "array",
            "items": [
                {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer"
                        },
                        "name": {
                            "type": "string"
                        },
                        "permissions": {
                            "type": "string",
                            "enum": ["none", "view", "download", "edit", "manage", "owner"]
                        },
                        "title": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "id",
                        "name",
                        "permissions",
                        "title"
                    ]
                }
            ]
        },
        "groups": {
            "type": "array",
            "items": [
                {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer"
                        },
                        "title": {
                            "type": "string"
                        },
                        "name": {
                            "type": "string"
                        },
                        "permissions": {
                            "type": "string",
                            "enum": ["none", "view", "download", "edit", "manage", "owner"]
                        }
                    },
                    "required": [
                        "id",
                        "title",
                        "name",
                        "permissions"
                    ]
                }
            ]
        }
    },
    "required": [
        "users",
        "organizations",
        "groups"
    ]
}


def _to_extended_perms(perm: str, resource_type: str = None, resource_storeType: str = None, is_owner: bool = False) -> list:
    """Explode "compact" permissions into an "extended" set, accordingly to the schema below:

      - view: view resource
      - download: view and download
      - edit: view download and edit (metadata, style, data)
      - manage: change permissions, delete resource, etc.
      - owner: admin permissions
    """
    if is_owner:
        if resource_type and resource_type.lower() in DOWNLOADABLE_RESOURCES:
            if resource_storeType and resource_storeType in DATA_EDITABLE_RESOURCES_SUBTYPES:
                return LAYER_ADMIN_PERMISSIONS + OWNER_PERMISSIONS + DOWNLOAD_PERMISSIONS
            else:
                return OWNER_PERMISSIONS + DOWNLOAD_PERMISSIONS
        else:
            return OWNER_PERMISSIONS
    elif perm is None or len(perm) == 0 or perm == NONE_RIGHTS:
        return []
    elif perm == VIEW_RIGHTS:
        return VIEW_PERMISSIONS
    elif perm == DOWNLOAD_RIGHTS:
        if resource_type and resource_type.lower() in DOWNLOADABLE_RESOURCES:
            return VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS
        else:
            return VIEW_PERMISSIONS
    elif perm == EDIT_RIGHTS:
        if resource_type and resource_type.lower() in DOWNLOADABLE_RESOURCES:
            if resource_storeType and resource_storeType in DATA_EDITABLE_RESOURCES_SUBTYPES:
                return LAYER_ADMIN_PERMISSIONS + VIEW_PERMISSIONS + EDIT_PERMISSIONS + DOWNLOAD_PERMISSIONS
            else:
                return VIEW_PERMISSIONS + EDIT_PERMISSIONS + DOWNLOAD_PERMISSIONS
        else:
            return VIEW_PERMISSIONS + EDIT_PERMISSIONS
    elif perm == MANAGE_RIGHTS:
        if resource_type and resource_type.lower() in DOWNLOADABLE_RESOURCES:
            if resource_storeType and resource_storeType in DATA_EDITABLE_RESOURCES_SUBTYPES:
                return LAYER_ADMIN_PERMISSIONS + VIEW_PERMISSIONS + ADMIN_PERMISSIONS + DOWNLOAD_PERMISSIONS
            else:
                return VIEW_PERMISSIONS + ADMIN_PERMISSIONS + DOWNLOAD_PERMISSIONS
        else:
            return VIEW_PERMISSIONS + ADMIN_PERMISSIONS


def _to_compact_perms(perms: list, resource_type: str = None, resource_storeType: str = None, is_owner: bool = False) -> str:
    """Compress standard permissions into a "compact" set, accordingly to the schema below:

      - view: view resource
      - download: view and download
      - edit: view download and edit (metadata, style, data)
      - manage: change permissions, delete resource, etc.
      - owner: admin permissions
    """
    if is_owner:
        return OWNER_RIGHTS
    if perms is None or len(perms) == 0:
        return NONE_RIGHTS
    if any(_p in MANAGE_PERMISSIONS for _p in perms):
        return MANAGE_RIGHTS
    elif resource_type and resource_type.lower() in DOWNLOADABLE_RESOURCES and any(_p in LAYER_ADMIN_PERMISSIONS + EDIT_PERMISSIONS for _p in perms):
        return EDIT_RIGHTS
    elif any(_p in LAYER_ADMIN_PERMISSIONS + EDIT_PERMISSIONS for _p in perms):
        return EDIT_RIGHTS
    elif resource_type and resource_type.lower() in DOWNLOADABLE_RESOURCES and any(_p in DOWNLOAD_PERMISSIONS for _p in perms):
        return DOWNLOAD_RIGHTS
    elif any(_p in VIEW_PERMISSIONS for _p in perms):
        return VIEW_RIGHTS
    return NONE_RIGHTS


_Binding = collections.namedtuple('Binding', [
    'name', 'expected', 'ro', 'binding'
])

_User = collections.namedtuple('User', [
    'id', 'username', 'last_name', 'first_name', 'avatar', 'is_superuser', 'is_staff'
])

_Group = collections.namedtuple('Group', [
    'id', 'title', 'name', 'logo'
])


def _binding(name, expected=True, ro=True, binding=None):
    return _Binding(name, expected, ro, binding)


class BindingFailed(Exception):
    '''Something in the API has changed'''
    pass


class PermSpecConverterBase(object):

    _object_name = None

    def __init__(self, json, resource, parent=None):
        self._resource = resource
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
                if issubclass(binding.binding, PermSpecConverterBase):
                    if isinstance(val, list):
                        val = [binding.binding(v, getattr(self, '_resource', None), parent=self) for v in val]
                    else:
                        val = binding.binding(val, getattr(self, '_resource', None), parent=self)
                else:
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
                    "permissions": "manage",
                    "is_superuser": <bool>,
                    "is_staff": <bool>
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
        json = {}
        user_perms = []
        group_perms = []
        anonymous_perms = None
        contributors_perms = None
        organization_perms = []

        for _k in self.users:
            _perms = self.users[_k]
            if isinstance(_k, str):
                _k = get_user_model().objects.get(username=_k)
            if not _k.is_anonymous and _k.username != 'AnonymousUser':
                avatar = build_absolute_uri(avatar_url(_k, 240))
                user = _User(_k.id, _k.username, _k.last_name, _k.first_name, avatar, _k.is_superuser, _k.is_staff)
                is_owner = _k == self._resource.owner
                user_perms.append(
                    {
                        'id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'avatar': user.avatar,
                        'permissions': _to_compact_perms(_perms, self._resource.resource_type, getattr(self._resource, 'storeType', None), is_owner),
                        'is_superuser': user.is_superuser,
                        'is_staff': user.is_staff
                    }
                )
            else:
                anonymous_perms = {
                    'id': Group.objects.get(name='anonymous').id,
                    'title': 'anonymous',
                    'name': 'anonymous',
                    'permissions': _to_compact_perms(_perms, self._resource.resource_type, getattr(self._resource, 'storeType', None))
                }
        # Let's make sure we don't lose control over the resource
        if not any([_u.get('id', None) == self._resource.owner.id for _u in user_perms]):
            user_perms.append(
                {
                    'id': self._resource.owner.id,
                    'username': self._resource.owner.username,
                    'first_name': self._resource.owner.first_name,
                    'last_name': self._resource.owner.last_name,
                    'avatar': build_absolute_uri(avatar_url(self._resource.owner, 240)),
                    'permissions': OWNER_RIGHTS,
                    'is_superuser': self._resource.owner.is_superuser,
                    'is_staff': self._resource.owner.is_staff
                }
            )
        for user in get_user_model().objects.filter(is_superuser=True):
            if not any([_u.get('id', None) == user.id for _u in user_perms]):
                user_perms.append(
                    {
                        'id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'avatar': build_absolute_uri(avatar_url(user, 240)),
                        'permissions': MANAGE_RIGHTS,
                        'is_superuser': user.is_superuser,
                        'is_staff': user.is_staff
                    }
                )

        for _k in self.groups:
            _perms = self.groups[_k]
            if isinstance(_k, str):
                _k = Group.objects.get(name=_k)
            if _k.name == 'anonymous':
                anonymous_perms = {
                    'id': _k.id,
                    'title': 'anonymous',
                    'name': 'anonymous',
                    'permissions': _to_compact_perms(_perms, self._resource.resource_type, getattr(self._resource, 'storeType', None))
                }
            elif hasattr(_k, 'groupprofile'):
                group = _Group(_k.id, _k.groupprofile.title, _k.name, _k.groupprofile.logo_url)
                if _k.name == groups_settings.REGISTERED_MEMBERS_GROUP_NAME:
                    contributors_perms = {
                        'id': group.id,
                        'title': group.title,
                        'name': group.name,
                        'permissions': _to_compact_perms(_perms, self._resource.resource_type, getattr(self._resource, 'storeType', None))
                    }
                else:
                    organization_perms.append(
                        {
                            'id': group.id,
                            'title': group.title,
                            'name': group.name,
                            'logo': group.logo,
                            'permissions': _to_compact_perms(_perms, self._resource.resource_type, getattr(self._resource, 'storeType', None))
                        }
                    )

        if anonymous_perms:
            group_perms.append(anonymous_perms)
        else:
            anonymous_group = Group.objects.get(name='anonymous')
            group_perms.append(
                {
                    'id': anonymous_group.id,
                    'title': 'anonymous',
                    'name': 'anonymous',
                    'permissions': _to_compact_perms(
                        get_group_perms(anonymous_group, self._resource),
                        self._resource.resource_type,
                        getattr(self._resource, 'storeType', None))
                }
            )
        if contributors_perms:
            group_perms.append(contributors_perms)
        elif Group.objects.filter(name=groups_settings.REGISTERED_MEMBERS_GROUP_NAME).exists():
            contributors_group = Group.objects.get(name=groups_settings.REGISTERED_MEMBERS_GROUP_NAME)
            group_perms.append(
                {
                    'id': contributors_group.id,
                    'title': 'Registered Members',
                    'name': contributors_group.name,
                    'permissions': _to_compact_perms(
                        get_group_perms(contributors_group, self._resource),
                        self._resource.resource_type, getattr(self._resource, 'storeType', None))
                }
            )

        json['users'] = user_perms
        json['organizations'] = organization_perms
        json['groups'] = group_perms
        return json.copy()


class PermSpecUserCompact(PermSpecConverterBase):

    _object_name = 'perm_spec_user_compact'
    _bindings = (
        _binding('id'),
        _binding('username', expected=False),
        _binding('first_name', expected=False),
        _binding('last_name', expected=False),
        _binding('avatar', expected=False),
        _binding('permissions'),
        _binding('is_superuser', expected=False),
        _binding('is_staff', expected=False)
    )


class PermSpecGroupCompact(PermSpecConverterBase):

    _object_name = 'perm_spec_group_compact'
    _bindings = (
        _binding('id'),
        _binding('title', expected=False),
        _binding('name', expected=False),
        _binding('logo', expected=False),
        _binding('permissions'),
    )


class PermSpecCompact(PermSpecConverterBase):

    _object_name = 'perm_spec_compact'
    _bindings = (
        _binding('users', expected=False, binding=PermSpecUserCompact),
        _binding('organizations', expected=False, binding=PermSpecGroupCompact),
        _binding('groups', expected=False, binding=PermSpecGroupCompact),
    )

    @classmethod
    def validate(cls, perm_spec):
        try:
            jsonschema.validate(perm_spec, PERM_SPEC_COMPACT_SCHEMA)
            return True
        except jsonschema.ValidationError:
            return False

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
            _is_owner = _user_profile == self._resource.owner
            _perms = OWNER_RIGHTS if _is_owner else MANAGE_RIGHTS if _user_profile.is_superuser else _u.permissions
            json['users'][_user_profile.username] = _to_extended_perms(_perms, self._resource.resource_type, getattr(self._resource, 'storeType', None), _is_owner)
        for _go in self.organizations:
            _group = Group.objects.get(id=_go.id)
            json['groups'][_group.name] = _to_extended_perms(_go.permissions, self._resource.resource_type, getattr(self._resource, 'storeType', None))
        for _go in self.groups:
            _group = Group.objects.get(id=_go.id)
            json['groups'][_group.name] = _to_extended_perms(_go.permissions, self._resource.resource_type, getattr(self._resource, 'storeType', None))
            if _go.name == 'anonymous':
                _user_profile = get_anonymous_user()
                json['users'][_user_profile.username] = _to_extended_perms(_go.permissions, self._resource.resource_type, getattr(self._resource, 'storeType', None))
        return json.copy()

    def merge(self, perm_spec_compact_patch: "PermSpecCompact"):
        """Merges 'perm_spec_compact_patch' to the current one.

         - Existing elements will be overridden.
         - Non existing elements will be added.
         - If you need to delete elements you cannot use this method.
        """
        for _elem in [_b.name for _b in self._bindings]:
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


def get_compact_perms_list(perms: list,
                           resource_type: str = None,
                           resource_storeType: str = None,
                           is_owner: bool = False,
                           is_none_allowed: bool = True,
                           compact_perms_labels: dict = {}) -> list:
    """
    Transforms an extended "perm_spec" into a list of compact perms.
    """
    def _get_labeled_compact_perm(compact_perm: str):
        return {
            "name": compact_perm,
            "label": compact_perms_labels.get(compact_perm, compact_perm)
        }

    _perms_list = []
    _perm = _to_compact_perms(perms, resource_type, resource_storeType, is_owner)
    if _perm:
        for _p in COMPACT_RIGHT_MODES:
            if (_p[1] not in [DOWNLOAD_RIGHTS] + LAYER_ADMIN_PERMISSIONS or
                    _p[1] in [DOWNLOAD_RIGHTS] and any(__p in DOWNLOAD_PERMISSIONS for __p in perms) or
                    _p[1] in LAYER_ADMIN_PERMISSIONS and any(__p in DATA_EDITABLE_RESOURCES_SUBTYPES for __p in perms)):
                _perms_list.append(_get_labeled_compact_perm(_p[1]))
                if _p[1] == _perm:
                    break
    if is_owner and OWNER_RIGHTS not in _perms_list:
        _perms_list.append(_get_labeled_compact_perm(OWNER_RIGHTS))
    if is_none_allowed and NONE_RIGHTS not in _perms_list:
        _perms_list.insert(0, _get_labeled_compact_perm(NONE_RIGHTS))
    return _perms_list
