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

from django.db import models
from django.urls import reverse
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _
from django_jsonfield_backport.models import JSONField

from guardian.shortcuts import get_anonymous_user

from geonode.base.models import ResourceBase, resourcebase_post_save

logger = logging.getLogger("geonode.geoapps.models")


class GeoApp(ResourceBase):

    """
    A GeoApp it is a generic container for every client applications the
    user might want to create or define.
    """

    PERMISSIONS = {
        'write': [
            'change_geoapp_data',
            'change_geoapp_style',
        ]
    }

    name = models.TextField(_('Name'), unique=True, db_index=True)

    # viewer configuration
    zoom = models.IntegerField(_('zoom'), null=True, blank=True)
    # The zoom level to use when initially loading this geoapp.  Zoom levels start
    # at 0 (most zoomed out) and each increment doubles the resolution.

    projection = models.CharField(_('projection'), max_length=32, null=True, blank=True)
    # The projection used for this geoapp.  This is stored as a string with the
    # projection's SRID.

    center_x = models.FloatField(_('center X'), null=True, blank=True)
    # The x coordinate to center on when loading this geoapp.  Its interpretation
    # depends on the projection.

    center_y = models.FloatField(_('center Y'), null=True, blank=True)
    # The y coordinate to center on when loading this geoapp.  Its interpretation
    # depends on the projection.

    last_modified = models.DateTimeField(auto_now_add=True)
    # The last time the geoapp was modified.

    urlsuffix = models.CharField(_('Site URL'), max_length=255, null=True, blank=True)
    # Alphanumeric alternative to referencing geoapps by id, appended to end of
    # URL instead of id, ie http://domain/geoapps/someview

    data = models.OneToOneField(
        "GeoAppData",
        related_name="data",
        null=True,
        blank=True,
        on_delete=models.CASCADE)

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
        if _child and hasattr(_child, 'app_type'):
            return _child.app_type
        return None

    @property
    def is_public(self):
        """
        Returns True if anonymous (public) user can view geoapp.
        """
        user = get_anonymous_user()
        return user.has_perm(
            'base.view_resourcebase',
            obj=self.resourcebase_ptr)

    @property
    def keywords_list(self):
        keywords_qs = self.keywords.all()
        if keywords_qs:
            return [kw.name for kw in keywords_qs]
        else:
            return []

    def get_absolute_url(self):
        geoapp_view = (
            reverse("geoapp_detail", None, [str(self.id)]) if settings.GEONODE_APPS_ENABLE else reverse("home")
        )
        return geoapp_view

    @property
    def embed_url(self):
        return reverse('geoapp_embed', kwargs={'geoappid': self.pk})

    class Meta(ResourceBase.Meta):
        pass


class GeoAppData(models.Model):

    blob = JSONField(
        null=False,
        default=dict)

    resource = models.ForeignKey(
        GeoApp,
        null=False,
        blank=False,
        on_delete=models.CASCADE)


# signals.pre_delete.connect(pre_delete_app, sender=GeoApp)
signals.post_save.connect(resourcebase_post_save, sender=GeoApp)
