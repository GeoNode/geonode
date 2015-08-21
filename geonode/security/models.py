# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

from django.contrib.auth import get_user_model

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import login
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from guardian.utils import get_user_obj_perms_model
from guardian.shortcuts import assign_perm, get_groups_with_perms


ADMIN_PERMISSIONS = [
    'view_resourcebase',
    'download_resourcebase',
    'change_resourcebase_metadata',
    'change_resourcebase',
    'delete_resourcebase',
    'change_resourcebase_permissions',
    'publish_resourcebase',
]

LAYER_ADMIN_PERMISSIONS = [
    'change_layer_data',
    'change_layer_style'
]


def get_users_with_perms(obj):
    """
    Override of the Guardian get_users_with_perms
    """
    ctype = ContentType.objects.get_for_model(obj)
    permissions = {}
    PERMISSIONS_TO_FETCH = ADMIN_PERMISSIONS + LAYER_ADMIN_PERMISSIONS

    for perm in Permission.objects.filter(codename__in=PERMISSIONS_TO_FETCH, content_type_id=ctype.id):
        permissions[perm.id] = perm.codename

    user_model = get_user_obj_perms_model(obj)
    users_with_perms = user_model.objects.filter(object_pk=obj.pk,
                                                 content_type_id=ctype.id,
                                                 permission_id__in=permissions).values('user_id', 'permission_id')

    users = {}
    for item in users_with_perms:
        if item['user_id'] in users:
            users[item['user_id']].append(permissions[item['permission_id']])
        else:
            users[item['user_id']] = [permissions[item['permission_id']], ]

    profiles = {}
    for profile in get_user_model().objects.filter(id__in=users.keys()):
        profiles[profile] = users[profile.id]

    return profiles


class PermissionLevelError(Exception):
    pass


class PermissionLevelMixin(object):

    """
    Mixin for adding "Permission Level" methods
    to a model class -- eg role systems where a
    user has exactly one assigned role with respect to
    an object representing an "access level"
    """

    def get_all_level_info(self):

        resource = self.get_self_resource()
        info = {
            'users': get_users_with_perms(
                resource),
            'groups': get_groups_with_perms(
                resource,
                attach_perms=True)}

        # TODO very hugly here, but isn't huglier
        # to set layer permissions to resource base?
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
                    info['groups'][group] = info['groups'][group] + info_layer['groups'][group]
                else:
                    info['groups'][group] = info_layer['groups'][group]

        return info

    def get_self_resource(self):
        return self.resourcebase_ptr if hasattr(
            self,
            'resourcebase_ptr_id') else self

    def set_default_permissions(self):
        """
        Remove all the permissions except for the owner and assign the
        view permission to the anonymous group
        """
        remove_object_permissions(self)

        # default permissions for anonymous users
        anonymous_group, created = Group.objects.get_or_create(name='anonymous')
        if settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION:
            assign_perm('view_resourcebase', anonymous_group, self.get_self_resource())
        if settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION:
            assign_perm('download_resourcebase', anonymous_group, self.get_self_resource())

        # default permissions for resource owner
        set_owner_permissions(self)

        # only for layer owner
        if self.__class__.__name__ == 'Layer':
            assign_perm('change_layer_data', self.owner, self)
            assign_perm('change_layer_style', self.owner, self)

    def set_permissions(self, perm_spec):
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

        remove_object_permissions(self)

        if 'users' in perm_spec and "AnonymousUser" in perm_spec['users']:
            anonymous_group = Group.objects.get(name='anonymous')
            for perm in perm_spec['users']['AnonymousUser']:
                assign_perm(perm, anonymous_group, self.get_self_resource())

        # TODO refactor code here
        if 'users' in perm_spec:
            for user, perms in perm_spec['users'].items():
                user = get_user_model().objects.get(username=user)
                for perm in perms:
                    if self.polymorphic_ctype.name == 'layer' and perm in (
                            'change_layer_data', 'change_layer_style',
                            'add_layer', 'change_layer', 'delete_layer',):
                        assign_perm(perm, user, self.layer)
                    else:
                        assign_perm(perm, user, self.get_self_resource())

        if 'groups' in perm_spec:
            for group, perms in perm_spec['groups'].items():
                group = Group.objects.get(name=group)
                for perm in perms:
                    if self.polymorphic_ctype.name == 'layer' and perm in (
                            'change_layer_data', 'change_layer_style',
                            'add_layer', 'change_layer', 'delete_layer',):
                        assign_perm(perm, group, self.layer)
                    else:
                        assign_perm(perm, group, self.get_self_resource())

        # default permissions for resource owner
        set_owner_permissions(self)


def set_owner_permissions(resource):
    """assign all admin permissions to the owner"""
    if resource.polymorphic_ctype.name == 'layer':
        for perm in LAYER_ADMIN_PERMISSIONS:
            assign_perm(perm, resource.owner, resource.layer)
    for perm in ADMIN_PERMISSIONS:
            assign_perm(perm, resource.owner, resource.get_self_resource())


def remove_object_permissions(instance):
    """Remove object perimssions on give resource.
        If is a layer removes the layer specific permissions then the resourcebase permissions
    """
    from guardian.models import UserObjectPermission, GroupObjectPermission

    if hasattr(instance, "layer"):
        UserObjectPermission.objects.filter(content_type=ContentType.objects.get_for_model(instance),
                                            object_pk=instance.id).delete()
        GroupObjectPermission.objects.filter(content_type=ContentType.objects.get_for_model(instance),
                                             object_pk=instance.id).delete()

    resource = instance.get_self_resource()
    UserObjectPermission.objects.filter(content_type=ContentType.objects.get_for_model(resource),
                                        object_pk=instance.id).delete()
    GroupObjectPermission.objects.filter(content_type=ContentType.objects.get_for_model(resource),
                                         object_pk=instance.id).delete()


# Logic to login a user automatically when it has successfully
# activated an account:
def autologin(sender, **kwargs):
    user = kwargs['user']
    request = kwargs['request']
    # Manually setting the default user backed to avoid the
    # 'User' object has no attribute 'backend' error
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    # This login function does not need password.
    login(request, user)

# FIXME(Ariel): Replace this signal with the one from django-user-accounts
# user_activated.connect(autologin)
