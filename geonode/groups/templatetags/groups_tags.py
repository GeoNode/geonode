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
from django import template
from django.contrib.staticfiles.storage import staticfiles_storage

register = template.Library()


@register.simple_tag
def group_profile_image(group_profile, css_classes="", size=None):
    """Returns an HTML img tag with the input group_profiles's logo.

    If the group profile does not have an associated logo, a stock image is
    used.

    """

    if isinstance(css_classes, str):
        class_attr = f'class="{css_classes}" '
    else:
        try:
            class_attr = f'class="{(" ".join(str(i) for i in css_classes))}" '
        except Exception:
            class_attr = ""
    if size is not None:
        style_attr = f'style="width: {size}px; height: {size}px" '
    else:
        style_attr = ""

    if group_profile.logo.name:
        url = group_profile.logo_url
    else:
        url = staticfiles_storage.url("geonode/img/default-avatar.jpg")
    img_tag = f'<img {class_attr}{style_attr}src="{url}" alt="{group_profile.title}">'
    return img_tag
