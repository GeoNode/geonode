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
from imagekit.models import ImageSpecField

from django.db import models
from django.core.cache import cache
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_noop as _
from django.db.models.signals import post_save, post_delete

THEME_CACHE_KEY = 'enabled_theme'


class JumbotronThemeSlide(models.Model):
    slide_name = models.CharField(max_length=255, unique=True)
    jumbotron_slide_image = models.ImageField(
        upload_to='img/%Y/%m', verbose_name="Jumbotron slide background")
    jumbotron_slide_image_thumbnail = ImageSpecField(
        source='jumbotron_slide_image', options={'quality': 60})
    jumbotron_slide_content = models.TextField(
        null=True, blank=True, verbose_name="Jumbotron slide content",
        help_text=_("Fill in this section with markdown"))
    hide_jumbotron_slide_content = models.BooleanField(
        default=False,
        verbose_name="Hide text in the jumbotron slide",
        help_text=_("Check this if the jumbotron background image already contains text"))
    is_enabled = models.BooleanField(
        default=True,
        help_text=_("Disabling this slide will hide it from the slide show"))

    def __str__(self):
        get_icon = (lambda arg: '[✓]' if arg else '[✗]')
        _enabled_icon = get_icon(self.is_enabled)
        _slide_content_icon = get_icon(self.hide_jumbotron_slide_content)
        return f'{self.slide_name} | <Enabled: {_enabled_icon} -- Hide Text: {_slide_content_icon}>'


class GeoNodeThemeCustomization(models.Model):
    date = models.DateTimeField(auto_now_add=True, blank=True, help_text="This will not appear anywhere.")
    name = models.CharField(max_length=100, help_text="This will not appear anywhere.")
    description = models.TextField(null=True, blank=True, help_text="This will not appear anywhere.")
    is_enabled = models.BooleanField(
        default=False,
        help_text="Enabling this theme will disable the current enabled theme (if any)")
    logo = models.ImageField(upload_to='img/%Y/%m', null=True, blank=True)
    extra_css = models.TextField(
        null=True,
        blank=True,
        verbose_name="Custom CSS rules",
        help_text="This field can be used to insert additional css rules. For example they can be used to customise the Mapstore client custom_theme.html template)"
    )
    jumbotron_bg = models.ImageField(
        upload_to='img/%Y/%m', null=True, blank=True, verbose_name="Jumbotron background")
    jumbotron_welcome_hide = models.BooleanField(
        default=False,
        verbose_name="Hide text in the jumbotron",
        help_text="Check this if the jumbotron backgroud image already contains text")
    welcome_theme = models.CharField(max_length=255, default="JUMBOTRON_BG",
                                     choices=(("JUMBOTRON_BG", "jumbotron background"), ("SLIDE_SHOW", "slide show"),),
                                     help_text=_("Choose between using jumbotron background and slide show"))
    jumbotron_slide_show = models.ManyToManyField(JumbotronThemeSlide, blank=True)
    jumbotron_welcome_title = models.CharField(max_length=255, null=True, blank=True, verbose_name="Jumbotron title")
    jumbotron_welcome_content = models.TextField(null=True, blank=True, verbose_name="Jumbotron content")

    @property
    def theme_uuid(self):
        if not self.identifier:
            self.identifier = slugify(f"theme id {self.id} {self.date}")
        return str(self.identifier)

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ("date", )
        verbose_name_plural = 'Themes'


# Disable other themes if one theme is enabled.
@receiver(post_save, sender=GeoNodeThemeCustomization)
def disable_other(sender, instance, **kwargs):
    if instance.is_enabled:
        GeoNodeThemeCustomization.objects.exclude(pk=instance.pk).update(is_enabled=False)


# Invalidate the cached theme if a theme is updated.
@receiver(post_save, sender=GeoNodeThemeCustomization)
@receiver(post_delete, sender=GeoNodeThemeCustomization)
def invalidate_cache(sender, instance, **kwargs):
    cache.delete(THEME_CACHE_KEY)
