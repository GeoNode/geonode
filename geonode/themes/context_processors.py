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
from django.core.cache import cache

from .models import GeoNodeThemeCustomization, THEME_CACHE_KEY


def custom_theme(request):
    theme = cache.get(THEME_CACHE_KEY)
    if theme is None:
        try:
            theme = GeoNodeThemeCustomization.objects.get(is_enabled=True)
            slides = theme.jumbotron_slide_show.filter(is_enabled=True)
        except Exception:
            theme = {}
            slides = []
        cache.set(THEME_CACHE_KEY, theme)
    else:
        try:
            slides = theme.jumbotron_slide_show.filter(is_enabled=True)
        except Exception:
            slides = []
    return {'custom_theme': theme, 'slides': slides}
