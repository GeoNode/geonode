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


# Geonode functionality

import os
import ast
from django.db import models


class SingletonModel(models.Model):
    """
    Base, abstract class for django singleton models

    Note: when registering a Singleton model in admin panel, remember to restrict deletion permissions
    according to your requirements, since "delete selected objects" uses QuerysSet.delete() instead of
    Model.delete()
    """

    class Meta:
        abstract = True

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        val = os.getenv("FORCE_READ_ONLY_MODE", None)
        if val is not None:
            setattr(obj, "read_only", ast.literal_eval(val))
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        kwargs.update({"force_insert": False})
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass
