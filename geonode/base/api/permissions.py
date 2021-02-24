# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2020 OSGeo
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
from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import permissions
from rest_framework.filters import BaseFilterBackend

logger = logging.getLogger(__name__)


class IsSelf(permissions.BasePermission):

    """ Grant permission only if the current instance is the request user.
    Used to allow users to edit their own account, nothing to others (even
    superusers).
    """

    def has_permission(self, request, view):
        """ Always return True here.
        The fine-grained permissions are handled in has_object_permission().
        """

        return True

    def has_object_permission(self, request, view, obj):
        return obj.id == request.user.id


class IsSelfOrReadOnly(IsSelf):

    """ Grant permissions if instance *IS* the request user, or read-only.
    Used to allow users to edit their own account, and others to read.
    """

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True

        return IsSelf.has_object_permission(self, request, view, obj)


class IsSelfOrAdmin(IsSelf):

    """ Grant R/W to self and superusers/staff members. Deny others. """

    def has_object_permission(self, request, view, obj):

        user = request.user

        if user.is_superuser or user.is_staff:
            return True

        return IsSelf.has_object_permission(self, request, view, obj)


class IsSelfOrAdminOrReadOnly(IsSelfOrAdmin):

    """ Grant R/W to self and superusers/staff members, R/O to others. """

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True

        return IsSelfOrAdmin.has_object_permission(self, request, view, obj)


class IsSelfOrAdminOrAuthenticatedReadOnly(IsSelfOrAdmin):

    """ Grant R/W to self and superusers/staff members, R/O to auth. """

    def has_object_permission(self, request, view, obj):

        user = request.user

        if request.method in permissions.SAFE_METHODS:
            if user.is_authenticated():
                return True

        return IsSelfOrAdmin.has_object_permission(self, request, view, obj)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    def has_object_permission(self, request, view, obj):
        if request.user is None or \
        (not request.user.is_anonymous and not request.user.is_active):
            return False
        if request.user.is_superuser:
            return True

        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS and not isinstance(obj, get_user_model()):
            return True

        # Instance must have an attribute named `owner`.
        if isinstance(obj, get_user_model()) and obj == request.user:
            return True
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        else:
            return False


class ResourceBasePermissionsFilter(BaseFilterBackend):
    """
    A filter backend that limits results to those where the requesting user
    has read object level permissions.
    """
    shortcut_kwargs = {
        'accept_global_perms': True,
    }

    def filter_queryset(self, request, queryset, view):
        # We want to defer this import until runtime, rather than import-time.
        # See https://github.com/encode/django-rest-framework/issues/4608
        # (Also see #1624 for why we need to make this import explicitly)
        from guardian.shortcuts import get_objects_for_user
        from geonode.base.models import ResourceBase
        from geonode.security.utils import get_visible_resources

        user = request.user
        # perm_format = '%(app_label)s.view_%(model_name)s'
        # permission = self.perm_format % {
        #     'app_label': queryset.model._meta.app_label,
        #     'model_name': queryset.model._meta.model_name,
        # }

        if settings.SKIP_PERMS_FILTER:
            resources = ResourceBase.objects.all()
        else:
            resources = get_objects_for_user(
                user,
                'base.view_resourcebase',
                **self.shortcut_kwargs
            )
        logger.debug(f" user: {user} -- resources: {resources}")

        obj_with_perms = get_visible_resources(
            resources,
            user,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)
        logger.debug(f" user: {user} -- obj_with_perms: {obj_with_perms}")

        return queryset.filter(id__in=obj_with_perms.values('id'))
