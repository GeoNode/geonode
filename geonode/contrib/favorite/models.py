# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.maps.models import Map


class FavoriteManager(models.Manager):
    def favorites_for_user(self, user):
        return self.filter(user=user)

    def _favorite_ct_for_user(self, user, model):
        content_type = ContentType.objects.get_for_model(model)
        return self.favorites_for_user(user).filter(content_type=content_type).prefetch_related('content_object')

    def favorite_documents_for_user(self, user):
        return self._favorite_ct_for_user(user, Document)

    def favorite_maps_for_user(self, user):
        return self._favorite_ct_for_user(user, Map)

    def favorite_layers_for_user(self, user):
        return self._favorite_ct_for_user(user, Layer)

    def favorite_users_for_user(self, user):
        return self._favorite_ct_for_user(user, get_user_model())

    def favorite_for_user_and_content_object(self, user, content_object):
        """
        if Favorite exists for input user and type and pk of the input
        content_object, return it.  else return None.
        impl note: can only be 0 or 1, per the class's unique_together.
        """
        content_type = ContentType.objects.get_for_model(type(content_object))
        result = self.filter(user=user, content_type=content_type, object_id=content_object.pk)

        if len(result) > 0:
            return result[0]
        else:
            return None

    def bulk_favorite_objects(self, user):
        'get the actual favorite objects for a user as a dict by content_type'
        favs = {}
        for m in (Document, Map, Layer, get_user_model()):
            ct = ContentType.objects.get_for_model(m)
            f = self.favorites_for_user(user).filter(content_type=ct)
            favs[ct.name] = m.objects.filter(id__in=f.values('object_id'))
        return favs

    def create_favorite(self, content_object, user):
        content_type = ContentType.objects.get_for_model(type(content_object))
        favorite, _ = self.get_or_create(
            user=user,
            content_type=content_type,
            object_id=content_object.pk,
            )
        return favorite


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    created_on = models.DateTimeField(auto_now_add=True)

    objects = FavoriteManager()

    class Meta:
        verbose_name = 'favorite'
        verbose_name_plural = 'favorites'
        unique_together = (('user', 'content_type', 'object_id'),)

    def __unicode__(self):
        return "Favorite: {}, {}, {}".format(self.content_object.title, self.content_type, self.user)
