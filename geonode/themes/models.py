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
from django.utils.translation import ugettext_noop as _
from imagekit.models import ImageSpecField


THEME_CACHE_KEY = 'enabled_theme'


class Partner(models.Model):
    logo = models.ImageField(upload_to='img/%Y/%m', null=True, blank=True)
    name = models.CharField(max_length=100, help_text="This will not appear anywhere.")
    title = models.CharField(max_length=255, verbose_name="Display name")
    href = models.CharField(max_length=255, verbose_name="Website")

    @property
    def logo_class(self):
        _logo_class = slugify(f"logo_{self.name}")
        return f"{_logo_class}"

    @property
    def partner_link(self):
        _href = self.href if self.href.startswith('http') else f'http://{self.href}'
        return f"{_href}"

    def __str__(self):
        return f"{self.title}"

    class Meta:
        ordering = ("name", )
        verbose_name_plural = 'Partners'


class JumbotronThemeSlide(models.Model):
    slide_name = models.CharField(max_length=255, unique=True)
    jumbotron_slide_image = models.ImageField(
        upload_to='img/%Y/%m', verbose_name="Jumbotron slide background")
    jumbotron_slide_image_thumbnail = ImageSpecField(source='jumbotron_slide_image', options={'quality': 60})
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
        return '{} | <Enabled: {} -- Hide Text: {}>'.format(
            self.slide_name, get_icon(self.is_enabled), get_icon(self.hide_jumbotron_slide_content))


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
    welcome_theme = models.CharField(max_length=255, default="JUMBOTRON_BG",
                                     choices=(("JUMBOTRON_BG", "jumbotron background"), ("SLIDE_SHOW", "slide show"),),
                                     help_text=_("Choose between using jumbotron background and slide show"))
    jumbotron_slide_show = models.ManyToManyField(JumbotronThemeSlide, blank=True)
    jumbotron_welcome_title = models.CharField(max_length=255, null=True, blank=True, verbose_name="Jumbotron title")
    jumbotron_welcome_content = models.TextField(null=True, blank=True, verbose_name="Jumbotron content")
    jumbotron_cta_hide = models.BooleanField(default=False, blank=True, verbose_name="Hide call to action")
    jumbotron_cta_text = models.CharField(max_length=255, null=True, blank=True, verbose_name="Call to action text")
    jumbotron_cta_link = models.CharField(max_length=255, null=True, blank=True, verbose_name="Call to action link")
    body_color = models.CharField(max_length=10, default="#333333")
    body_text_color = models.CharField(max_length=10, default="#3a3a3a")
    navbar_color = models.CharField(max_length=10, default="#333333")
    navbar_text_color = models.CharField(max_length=10, default="#ffffff")
    navbar_text_hover = models.CharField(max_length=10, default="#2c689c")
    navbar_text_hover_focus = models.CharField(max_length=10, default="#2c689c")
    navbar_dropdown_menu = models.CharField(max_length=10, default="#2c689c")
    navbar_dropdown_menu_text = models.CharField(max_length=10, default="#ffffff")
    navbar_dropdown_menu_hover = models.CharField(max_length=10, default="#204d74")
    navbar_dropdown_menu_divider = models.CharField(max_length=10, default="#204d74")
    jumbotron_color = models.CharField(max_length=10, default="#2c689c")
    jumbotron_title_color = models.CharField(max_length=10, default="#ffffff")
    jumbotron_text_color = models.CharField(max_length=10, default="#ffffff")
    search_bg_color = models.CharField(max_length=10, default="#333333")
    search_title_color = models.CharField(max_length=10, default="#ffffff")
    search_link_color = models.CharField(max_length=10, default="#ff8f31")
    contactus = models.BooleanField(default=False, verbose_name="Enable contact us box")
    contact_name = models.CharField(max_length=255, null=True, blank=True)
    contact_position = models.CharField(max_length=255, null=True, blank=True)
    contact_administrative_area = models.CharField(max_length=255, null=True, blank=True)
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
    footer_bg_color = models.CharField(max_length=10, default="#333333")
    footer_text_color = models.CharField(max_length=10, default="#ffffff")
    footer_href_color = models.CharField(max_length=10, default="#ff8f31")

    # Cookies Law Info Bar
    cookie_law_info_bar_enabled = models.BooleanField(default=True, verbose_name="Cookies Law Info Bar")
    cookie_law_info_bar_head = models.TextField(null=False, blank=False, default="This website uses cookies")
    cookie_law_info_bar_text = models.TextField(
        null=False, blank=False,
        default="""This website uses cookies to improve your experience, \
        check <strong><a style="color:#000000" href="/privacy_cookies/">this page</a></strong> for details. \
        We'll assume you're ok with this, but you can opt-out if you wish.""")
    cookie_law_info_leave_url = models.TextField(null=False, blank=False, default="#")
    cookie_law_info_showagain_head = models.TextField(null=False, blank=False, default="Privacy & Cookies Policy")

    cookie_law_info_data_controller = models.TextField(null=False, blank=False, default="#DATA_CONTROLLER")
    cookie_law_info_data_controller_address = models.TextField(
        null=False, blank=False, default="#DATA_CONTROLLER_ADDRESS")
    cookie_law_info_data_controller_phone = models.TextField(null=False, blank=False, default="#DATA_CONTROLLER_PHONE")
    cookie_law_info_data_controller_email = models.TextField(null=False, blank=False, default="#DATA_CONTROLLER_EMAIL")

    # Cookies Law Info Bar settings
    cookie_law_info_animate_speed_hide = models.CharField(max_length=30, default="500")
    cookie_law_info_animate_speed_show = models.CharField(max_length=30, default="500")
    cookie_law_info_background = models.CharField(max_length=30, default="#2c689c")
    cookie_law_info_border = models.CharField(max_length=30, default="#444")
    cookie_law_info_border_on = models.CharField(max_length=30, default="false")
    cookie_law_info_button_1_button_colour = models.CharField(max_length=30, default="#000")
    cookie_law_info_button_1_button_hover = models.CharField(max_length=30, default="#000000")
    cookie_law_info_button_1_link_colour = models.CharField(max_length=30, default="#2c689c")
    cookie_law_info_button_1_as_button = models.CharField(max_length=30, default="true")
    cookie_law_info_button_1_new_win = models.CharField(max_length=30, default="true")
    cookie_law_info_button_2_button_colour = models.CharField(max_length=30, default="#000000")
    cookie_law_info_button_2_button_hover = models.CharField(max_length=30, default="#000000")
    cookie_law_info_button_2_link_colour = models.CharField(max_length=30, default="#2c689c")
    cookie_law_info_button_2_as_button = models.CharField(max_length=30, default="true")
    cookie_law_info_button_2_hidebar = models.CharField(max_length=30, default="true")
    cookie_law_info_button_3_button_colour = models.CharField(max_length=30, default="#000")
    cookie_law_info_button_3_button_hover = models.CharField(max_length=30, default="#000000")
    cookie_law_info_button_3_link_colour = models.CharField(max_length=30, default="#2c689c")
    cookie_law_info_button_3_as_button = models.CharField(max_length=30, default="true")
    cookie_law_info_button_3_new_win = models.CharField(max_length=30, default="false")
    cookie_law_info_button_4_button_colour = models.CharField(max_length=30, default="#000")
    cookie_law_info_button_4_button_hover = models.CharField(max_length=30, default="#000000")
    cookie_law_info_button_4_link_colour = models.CharField(max_length=30, default="#2c689c")
    cookie_law_info_button_4_as_button = models.CharField(max_length=30, default="true")
    cookie_law_info_font_family = models.CharField(max_length=30, default="inherit")
    cookie_law_info_header_fix = models.CharField(max_length=30, default="false")
    cookie_law_info_notify_animate_hide = models.CharField(max_length=30, default="true")
    cookie_law_info_notify_animate_show = models.CharField(max_length=30, default="false")
    cookie_law_info_notify_div_id = models.CharField(max_length=30, default="#cookie-law-info-bar")
    cookie_law_info_notify_position_horizontal = models.CharField(max_length=30, default="right")
    cookie_law_info_notify_position_vertical = models.CharField(max_length=30, default="bottom")
    cookie_law_info_scroll_close = models.CharField(max_length=30, default="false")
    cookie_law_info_scroll_close_reload = models.CharField(max_length=30, default="false")
    cookie_law_info_accept_close_reload = models.CharField(max_length=30, default="false")
    cookie_law_info_reject_close_reload = models.CharField(max_length=30, default="false")
    cookie_law_info_showagain_tab = models.CharField(max_length=30, default="true")
    cookie_law_info_showagain_background = models.CharField(max_length=30, default="#fff")
    cookie_law_info_showagain_border = models.CharField(max_length=30, default="#000")
    cookie_law_info_showagain_div_id = models.CharField(max_length=30, default="#cookie-law-info-again")
    cookie_law_info_showagain_x_position = models.CharField(max_length=30, default="30px")
    cookie_law_info_text = models.CharField(max_length=30, default="#ffffff")
    cookie_law_info_show_once_yn = models.CharField(max_length=30, default="false")
    cookie_law_info_show_once = models.CharField(max_length=30, default="10000")
    cookie_law_info_logging_on = models.CharField(max_length=30, default="false")
    cookie_law_info_as_popup = models.CharField(max_length=30, default="false")
    cookie_law_info_popup_overlay = models.CharField(max_length=30, default="true")
    cookie_law_info_bar_heading_text = models.CharField(max_length=30, default="This website uses cookies")
    cookie_law_info_cookie_bar_as = models.CharField(max_length=30, default="banner")
    cookie_law_info_popup_showagain_position = models.CharField(max_length=30, default="bottom-right")
    cookie_law_info_widget_position = models.CharField(max_length=30, default="left")

    def file_link(self):
        if self.logo:
            return f"<a href='{self.logo.url}'>download</a>"
        else:
            return "No attachment"

    file_link.allow_tags = True

    @property
    def theme_uuid(self):
        if not self.identifier:
            self.identifier = slugify(f"theme id {self.id} {self.date}")
        return f"{self.identifier}"

    def __str__(self):
        return f"{self.name}"

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
