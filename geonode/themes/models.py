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
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


THEME_CACHE_KEY = 'enabled_theme'


class Partner(models.Model):
    logo = models.ImageField(upload_to='img/%Y/%m', null=True, blank=True)
    name = models.CharField(max_length=100, help_text="This will not appear anywhere.")
    title = models.CharField(max_length=255, verbose_name="Display name")
    href = models.CharField(max_length=255, verbose_name="Website")

    @property
    def logo_class(self):
        _logo_class = slugify("logo_%s" % self.name)
        return u"{0}".format(_logo_class)

    @property
    def partner_link(self):
        _href = self.href if self.href.startswith('http') else 'http://%s' % self.href
        return u"{0}".format(_href)

    def __unicode__(self):
        return u"{0}".format(self.title)

    class Meta:
        ordering = ("name", )
        verbose_name_plural = 'Partners'


class GeoNodeThemeCustomization(models.Model):
    name = models.CharField(max_length=100, help_text="This will not appear anywhere.")
    date = models.DateTimeField(auto_now_add=True, blank=True, help_text="This will not appear anywhere.")
    description = models.TextField(null=True, blank=True, help_text="This will not appear anywhere.")
    is_enabled = models.BooleanField(
        default=False,
        help_text="Enabling this theme will disable the current enabled theme (if any)")
    logo = models.ImageField(upload_to='img/%Y/%m', null=True, blank=True)
    jumbotron_bg = models.ImageField(
        upload_to='img/%Y/%m', null=True, blank=True, verbose_name="Jumbotron background")
    jumbotron_welcome_hide = models.BooleanField(
        default=False,
        verbose_name="Hide text in the jumbotron",
        help_text="Check this if the jumbotron backgroud image already contains text")
    jumbotron_welcome_title = models.CharField(max_length=255, null=True, blank=True, verbose_name="Jumbotron title")
    jumbotron_welcome_content = models.TextField(null=True, blank=True, verbose_name="Jumbotron content")
    jumbotron_cta_hide = models.BooleanField(default=False, blank=True, verbose_name="Hide call to action")
    jumbotron_cta_text = models.CharField(max_length=255, null=True, blank=True, verbose_name="Call to action text")
    jumbotron_cta_link = models.CharField(max_length=255, null=True, blank=True, verbose_name="Call to action link")
    body_color = models.CharField(max_length=10, default="#333333")
    navbar_color = models.CharField(max_length=10, default="#333333")
    jumbotron_color = models.CharField(max_length=10, default="#2c689c")
    contactus = models.BooleanField(default=False, verbose_name="Enable contact us box")
    contact_name = models.CharField(max_length=255, null=True, blank=True)
    contact_position = models.CharField(max_length=255, null=True, blank=True)
    contact_administrative_area = models.CharField(max_length=255, null=True, blank=True)
    contact_city = models.CharField(max_length=255, null=True, blank=True)
    contact_street = models.CharField(max_length=255, null=True, blank=True)
    contact_postal_code = models.CharField(max_length=255, null=True, blank=True)
    contact_city = models.CharField(max_length=255, null=True, blank=True)
    contact_country = models.CharField(max_length=255, null=True, blank=True)
    contact_delivery_point = models.CharField(max_length=255, null=True, blank=True)
    contact_voice = models.CharField(max_length=255, null=True, blank=True)
    contact_facsimile = models.CharField(max_length=255, null=True, blank=True)
    contact_email = models.CharField(max_length=255, null=True, blank=True)
    partners_title = models.CharField(max_length=100, null=True, blank=True, default="Our Partners")
    partners = models.ManyToManyField(Partner, related_name="partners", blank=True)
    copyright = models.TextField(null=True, blank=True)
    copyright_color = models.CharField(max_length=10, default="#2c689c")

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


# Disable other themes if one theme is enabled.
@receiver(post_save, sender=GeoNodeThemeCustomization)
def disable_other(sender, instance, **kwargs):
    if instance.is_enabled:
        GeoNodeThemeCustomization.objects.exclude(pk=instance.pk).update(is_enabled=False)


# Invalidate the cached theme if a partner or a theme is updated.
@receiver(post_save, sender=GeoNodeThemeCustomization)
@receiver(post_save, sender=Partner)
@receiver(post_delete, sender=GeoNodeThemeCustomization)
@receiver(post_delete, sender=Partner)
def invalidate_cache(sender, instance, **kwargs):
    cache.delete(THEME_CACHE_KEY)
