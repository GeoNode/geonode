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
from .conf import settings


class HookProxy:
    def __getattr__(self, attr):
        if not isinstance(settings.GEONODE_CLIENT_HOOKSET, str):
            return getattr(settings.GEONODE_CLIENT_HOOKSET, attr)
        else:
            import importlib

            cls = settings.GEONODE_CLIENT_HOOKSET.split(".")
            module_name, class_name = (".".join(cls[:-1]), cls[-1])
            i = importlib.import_module(module_name)
            hook = getattr(i, class_name)()
            return getattr(hook, attr)


hookset = HookProxy()
