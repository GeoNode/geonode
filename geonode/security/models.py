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

from django.contrib.auth import login
from django.contrib.auth.models import Group

from guardian.shortcuts import assign_perm, remove_perm, \
    get_groups_with_perms, get_users_with_perms

ADMIN_PERMISSIONS = [
    'view_resourcebase',
    'change_resourcebase',
    'delete_resourcebase',
    'change_resourcebase_permissions'
]


class PermissionLevelError(Exception):
    pass


class PermissionLevelMixin(object):

    """
    Mixin for adding "Permission Level" methods
    to a model class -- eg role systems where a
    user has exactly one assigned role with respect to
    an object representing an "access level"
    """

    LEVEL_NONE = "_none"

    def get_all_level_info(self):
        resource = self.get_self_resource()
        info = {
            'users': get_users_with_perms(
                resource,
                attach_perms=True,
                with_superusers=True),
            'groups': get_groups_with_perms(
                resource,
                attach_perms=True)}
        return info

    def get_self_resource(self):
        return self.resourcebase_ptr if hasattr(
            self,
            'resourcebase_ptr') else self

    def remove_all_permissions(self):
        """
        Remove all the permissions for users and groups except for the resource owner
        """
        for user, perms in get_users_with_perms(self.get_self_resource(), attach_perms=True).iteritems():
            if not self.owner == user:
                for perm in perms:
                    remove_perm(perm, user, self.get_self_resource())

        for group, perms in get_groups_with_perms(self.get_self_resource(), attach_perms=True).iteritems():
            for perm in perms:
                remove_perm(perm, group, self.get_self_resource())

    def set_default_permissions(self):
        """
        Remove all the permissions except for the owner and assign the
        view permission to the anonymous group
        """
        self.remove_all_permissions()

        anonymous_group, created = Group.objects.get_or_create(name='anonymous')
        assign_perm('view_resourcebase', anonymous_group, self.get_self_resource())

        for perm in ADMIN_PERMISSIONS:
            assign_perm(perm, self.owner, self.get_self_resource())

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
        self.remove_all_permissions()

        if 'users' in perm_spec and "AnonymousUser" in perm_spec['users']:
            anonymous_group = Group.objects.get(name='anonymous')
            assign_perm(
                perm_spec['users']['AnonymousUser'][0],
                anonymous_group,
                self.get_self_resource())

        if 'users' in perm_spec:
            for user, perms in perm_spec['users'].items():
                user = get_user_model().objects.get(username=user)
                for perm in perms:
                    assign_perm(perm, user, self.get_self_resource())

        if 'groups' in perm_spec:
            for group, perms in perm_spec['groups'].items():
                group = Group.objects.get(name=group)
                for perm in perms:
                    assign_perm(perm, group, self.get_self_resource())


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
