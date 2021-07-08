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
import importlib

from django.conf import settings  # noqa
from django.core.exceptions import ImproperlyConfigured

from appconf import AppConf


def load_path_attr(path):
    i = path.rfind(".")
    module, attr = path[:i], path[i + 1:]
    try:
        mod = importlib.import_module(module)
    except ImportError as e:
        raise ImproperlyConfigured(f"Error importing {module}: '{e}'")
    try:
        attr = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured(f"Module '{module}' does not define a '{attr}'")
    return attr


def is_installed(package):
    try:
        __import__(package)
        return True
    except ImportError:
        return False


class GeoNodeClientAppConf(AppConf):

    LAYER_PREVIEW_LIBRARY = 'geonode'
    HOOKSET = "geonode.client.hooksets.BaseHookSet"

    def configure_hookset(self, value):
        return load_path_attr(value)()

    class Meta:
        prefix = "geonode_client"
