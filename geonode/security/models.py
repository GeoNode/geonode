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
from django.contrib.auth.models import User, Permission, Group as DjangoGroup
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


    def get_self_resource(self):
        return self.resourcebase_ptr if self.resourcebase_ptr else self

    def set_default_permissions(self):
        for user, perms in get_users_with_perms(self.get_self_resource(), attach_perms=True).iteritems():
            if not self.owner == user:
                for perm in perms:
                    remove_perm(perm, user, self.get_self_resource())


        for group, perms in get_groups_with_perms(self.get_self_resource(), attach_perms=True).iteritems():
            for perm in perms:
                remove_perm(perm, group, self.get_self_resource())

        assign_perm('view_resourcebase', get_anonymous_user(), self.get_self_resource())


    def set_permissions(self, perm_spec):
        """
        Sets an object's the permission levels based on the perm_spec JSON.


        the mapping looks like:
        {
            'anonymous': 'readonly',
            'authenticated': 'readwrite',
            'users': {
                <username>: 'admin'
                ...
            }
            'groups': [
                    (<groupname>, <permission_level>),
                    (<groupname2>, <permission_level>)
                ]
        }
        """
        if "authenticated" in perm_spec:
            try:
                authenticated_group = DjangoGroup.objects.get(name='authenticated')
            except Group.DoesNotExist:
                raise 'The authenticated groups was not found in the database'
            assign_perm(perm_spec['authenticated'], authenticated_group, self.get_self_resource())
        if "anonymous" in perm_spec:
            self.set_gen_level(ANONYMOUS_USERS, perm_spec['anonymous'])
        if isinstance(perm_spec['users'], dict): 
            perm_spec['users'] = perm_spec['users'].items()
        users = [n[0] for n in perm_spec['users']]
        excluded = users + [self.owner]
        existing = self.get_user_levels().exclude(user__username__in=excluded)
        existing.delete()
        for username, level in perm_spec['users']:
            user = User.objects.get(username=username)
            self.set_user_level(user, level)

        if "geonode.contrib.groups" in settings.INSTALLED_APPS:
            #TODO: Should this run in a transaction?
            excluded_groups = [g[0] for g in perm_spec.get('groups', list())]

            # Delete all group levels that do not exist in perm_spec.
            self.get_group_levels().exclude(group__slug__in=excluded_groups).delete()

            for group, level in perm_spec.get('groups', list()):
                group = Group.objects.get(slug=group)
                self.set_group_level(group, level)

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
