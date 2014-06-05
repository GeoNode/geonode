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

from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import login
if "geonode.contrib.groups" in settings.INSTALLED_APPS:
    from geonode.contrib.groups.models import Group

from guardian.shortcuts import assign_perm, get_perms, remove_perm, \
    get_groups_with_perms, get_users_with_perms
from guardian.utils import get_anonymous_user
from guardian.models import UserObjectPermission, GroupObjectPermission

from geonode.security.enumerations import GENERIC_GROUP_NAMES
from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS


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
            'users': get_users_with_perms(resource, attach_perms=True, with_superusers=True),
            'groups': get_groups_with_perms(resource, attach_perms=True)
        }
        return info

    def get_self_resource(self):
        return self.resourcebase_ptr if hasattr(self, 'resourcebase_ptr') else self

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
        view permission to the anonymous user
        """
        self.remove_all_permissions()

        assign_perm('view_resourcebase', get_anonymous_user(), self.get_self_resource())


    def set_permissions(self, perm_spec):
        """
        Sets an object's the permission levels based on the perm_spec JSON.


        the mapping looks like:
        {
            'users': {
                'AnonymousUser': ['perm1','perm2','perm3'],
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

        for user, perms in perm_spec['users'].items():
            if user == "AnonymousUser":
                user = get_anonymous_user()
            else:
                user = User.objects.get(username=user)
            for perm in perms:
                assign_perm(perm, user, self.get_self_resource())

        if "geonode.contrib.groups" in settings.INSTALLED_APPS:
            for group, perms in perm_spec['groups'].items():           
                group = Group.objects.get(slug=user)
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

#FIXME(Ariel): Replace this signal with the one from django-user-accounts
#user_activated.connect(autologin)
