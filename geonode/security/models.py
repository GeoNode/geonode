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

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import login

from geonode.security.enumerations import GENERIC_GROUP_NAMES

class ObjectRoleManager(models.Manager):
    def get_by_natural_key(self, codename, app_label, model):
        return self.get(
            codename=codename,
            content_type=ContentType.objects.get_by_natural_key(app_label, model)
        )

class ObjectRole(models.Model):
    """
    A bundle of object permissions representing
    the rights associated with having a
    particular role with respect to an object.
    """
    objects = ObjectRoleManager()

    title = models.CharField(_('title'), max_length=255)
    permissions = models.ManyToManyField(Permission, verbose_name=_('permissions'))
    codename = models.CharField(_('codename'), max_length=100, unique=True)
    content_type = models.ForeignKey(ContentType)
    list_order = models.IntegerField(help_text=_("Determines the order that roles are presented in the user interface."))

    def __unicode__(self):
        return "%s | %s" % (self.content_type, self.title)

    class Meta:
        unique_together = (('content_type', 'codename'),)

    def natural_key(self):
        return (self.codename,) + self.content_type.natural_key()

class UserObjectRoleMapping(models.Model):
    """
    represents assignment of a role to a particular user
    in the context of a specific object.
    """

    user = models.ForeignKey(User, related_name="role_mappings")

    object_ct = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('object_ct', 'object_id')

    role = models.ForeignKey(ObjectRole, related_name="user_mappings")

    def __unicode__(self):
        return u"%s | %s -> %s" % (
            unicode(self.object),
            unicode(self.user),
            unicode(self.role))

    class Meta:
        unique_together = (('user', 'object_ct', 'object_id', 'role'), )


class GenericObjectRoleMapping(models.Model):
    """
    represents assignment of a role to an arbitrary implicitly
    defined group of users (groups without explicit database representation)
    in the context of a specific object. eg 'all authenticated users'
    'anonymous users', 'users <as defined by some other service>'
    """

    subject = models.CharField(max_length=100, choices=sorted(GENERIC_GROUP_NAMES.items()))

    object_ct = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('object_ct', 'object_id')

    role = models.ForeignKey(ObjectRole, related_name="generic_mappings")

    def __unicode__(self):
        return u"%s | %s -> %s" % (
            unicode(self.object),
            unicode(GENERIC_GROUP_NAMES[self.subject]),
            unicode(self.role))

    class Meta:
        unique_together = (('subject', 'object_ct', 'object_id', 'role'), )


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

    @property
    def permission_levels(self):
        """
        A list of available levels in order.
        """
        levels = [self.LEVEL_NONE]
        content_type = ContentType.objects.get_for_model(self)
        for role in ObjectRole.objects.filter(content_type=content_type).order_by('list_order'):
            levels.append(role.codename)
        return levels

    def get_user_level(self, user):
        """
        get the permission level (if any) specifically assigned to the given user.
        Returns LEVEL_NONE to indicate no specific level has been assigned.
        """
        try:
            my_ct = ContentType.objects.get_for_model(self)
            mapping = UserObjectRoleMapping.objects.get(user=user, object_id=self.id, object_ct=my_ct)
            return mapping.role.codename
        except Exception:
            return self.LEVEL_NONE

    def set_user_level(self, user, level):
        """
        set the user's permission level to the level specified. if
        level is LEVEL_NONE, any existing level assignment is removed.
        """

        my_ct = ContentType.objects.get_for_model(self)
        if level == self.LEVEL_NONE:
            UserObjectRoleMapping.objects.filter(user=user, object_id=self.id, object_ct=my_ct).delete()
        else:
            # lookup new role...
            try:
                role = ObjectRole.objects.get(codename=level, content_type=my_ct)
            except ObjectDoesNotExist:
                raise PermissionLevelError("Invalid Permission Level (%s)" % level)
            # remove any existing mapping
            UserObjectRoleMapping.objects.filter(user=user, object_id=self.id, object_ct=my_ct).delete()
            # grant new level
            UserObjectRoleMapping.objects.create(user=user, object=self, role=role)

    def get_gen_level(self, gen_role):
        """
        get the permission level (if any) specifically assigned to the given generic
        group of users.  Returns LEVEL_NONE to indicate no specific level has been assigned.
        """

        try:
            my_ct = ContentType.objects.get_for_model(self)
            mapping = GenericObjectRoleMapping.objects.get(subject=gen_role, object_id=self.id, object_ct=my_ct)
            return mapping.role.codename
        except Exception:
            return self.LEVEL_NONE

    def set_gen_level(self, gen_role, level):
        """
        grant the permission level specified to the generic group of
        users specified.  if level is LEVEL_NONE, any existing assignment is
        removed.
        """

        my_ct = ContentType.objects.get_for_model(self)
        if level == self.LEVEL_NONE:
            GenericObjectRoleMapping.objects.filter(subject=gen_role, object_id=self.id, object_ct=my_ct).delete()
        else:
            try:
                role = ObjectRole.objects.get(codename=level, content_type=my_ct)
            except ObjectRole.DoesNotExist:
                raise PermissionLevelError("Invalid Permission Level (%s)" % level)
            # remove any existing mapping
            GenericObjectRoleMapping.objects.filter(subject=gen_role, object_id=self.id, object_ct=my_ct).delete()
            # grant new level
            GenericObjectRoleMapping.objects.create(subject=gen_role, object=self, role=role)

    def get_user_levels(self):
        ct = ContentType.objects.get_for_model(self)
        return UserObjectRoleMapping.objects.filter(object_id = self.id, object_ct = ct)

    def get_generic_levels(self):
        ct = ContentType.objects.get_for_model(self)
        return GenericObjectRoleMapping.objects.filter(object_id = self.id, object_ct = ct)

    def get_all_level_info(self):
        """
        returns a mapping indicating the permission levels
        of users, anonymous users any authenticated users that
        have specific permissions assigned to them.

        if a key is not present it indicates that no level
        has been assigned.

        the mapping looks like:
        {
            'anonymous': 'readonly',
            'authenticated': 'readwrite',
            'users': {
                <username>: 'admin'
                ...
            }
        }
        """
        my_ct = ContentType.objects.get_for_model(self)

        # get all user-specific permissions
        user_levels = {}
        for rm in UserObjectRoleMapping.objects.filter(object_id=self.id, object_ct=my_ct).all():
            user_levels[rm.user.username] = rm.role.codename

        levels = {}
        for rm in GenericObjectRoleMapping.objects.filter(object_id=self.id, object_ct=my_ct).all():
            levels[rm.subject] = rm.role.codename
        levels['users'] = user_levels

        return levels

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
