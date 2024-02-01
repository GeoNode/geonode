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

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from guardian.shortcuts import get_anonymous_user

from geonode.base.models import ResourceBase
from geonode.client.hooks import hookset

logger = logging.getLogger("geonode.geoapps.models")


class GeoApp(ResourceBase):
    """
    A GeoApp it is a generic container for every client applications the
    user might want to create or define.
    """

    PERMISSIONS = {
        "write": [
            "change_geoapp_data",
            "change_geoapp_style",
        ]
    }

    name = models.TextField(_("Name"), null=False, blank=False)

    last_modified = models.DateTimeField(auto_now_add=True)
    # The last time the geoapp was modified.

    def __str__(self):
        return f'{self.title} by {(self.owner.username if self.owner else "<Anonymous>")}'

    @property
    def class_name(self):
        return self.__class__.__name__

    @property
    def sender(self):
        return None

    @property
    def center(self):
        """
        A handy shortcut for the center_x and center_y properties as a tuple
        (read only)
        """
        return (self.center_x, self.center_y)

    @property
    def type(self):
        _ct = self.polymorphic_ctype
        _child = _ct.model_class().objects.filter(pk=self.id).first()
        if _child and hasattr(_child, "app_type"):
            return _child.app_type
        return None

    @property
    def is_public(self):
        """
        Returns True if anonymous (public) user can view geoapp.
        """
        user = get_anonymous_user()
        return user.has_perm("base.view_resourcebase", obj=self.resourcebase_ptr)

    @property
    def keywords_list(self):
        keywords_qs = self.keywords.all()
        if keywords_qs:
            return [kw.name for kw in keywords_qs]
        else:
            return []

    def get_absolute_url(self):
        return hookset.geoapp_detail_url(self)

    @property
    def embed_url(self):
        return reverse("geoapp_embed", kwargs={"geoappid": self.pk})
