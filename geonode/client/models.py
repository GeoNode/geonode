# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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

from django.db import models
from django.template.defaultfilters import slugify


class GeoNodeThemeCustomization(models.Model):
    identifier = models.CharField(max_length=255, editable=False)
    name = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True, blank=True)
    description = models.TextField(null=True, blank=True)
    is_enabled = models.BooleanField(default=False)
    logo = models.ImageField(upload_to='img/%Y/%m', null=True, blank=True)
    jumbotron_bg = models.ImageField(
        upload_to='img/%Y/%m', null=True, blank=True)
    body_color = models.CharField(max_length=10, default="#333333")
    navbar_color = models.CharField(max_length=10, default="#333333")
    jumbotron_color = models.CharField(max_length=10, default="#2c689c")
    copyright_color = models.CharField(max_length=10, default="#2c689c")
    contactus = models.BooleanField(default=False)
    copyright = models.TextField(null=True, blank=True)
    contact_name = models.TextField(null=True, blank=True)
    contact_position = models.TextField(null=True, blank=True)
    contact_administrative_area = models.TextField(null=True, blank=True)
    contact_city = models.TextField(null=True, blank=True)
    contact_street = models.TextField(null=True, blank=True)
    contact_postal_code = models.TextField(null=True, blank=True)
    contact_city = models.TextField(null=True, blank=True)
    contact_country = models.TextField(null=True, blank=True)
    contact_delivery_point = models.TextField(null=True, blank=True)
    contact_voice = models.TextField(null=True, blank=True)
    contact_facsimile = models.TextField(null=True, blank=True)
    contact_email = models.TextField(null=True, blank=True)

    def file_link(self):
        if self.logo:
            return "<a href='%s'>download</a>" % (self.logo.url,)
        else:
            return "No attachment"

    file_link.allow_tags = True

    @property
    def theme_uuid(self):
        if not self.identifier:
            self.identifier = slugify("theme id %s %s" % (self.id, self.date))
        return u"{0}".format(self.identifier)

    def __unicode__(self):
        return u"{0}".format(self.name)

    class Meta:
        ordering = ("date", )
        verbose_name_plural = 'Themes'
