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

import os

__version__ = (5, 1, 0, 'final', 0)


def get_version():
    import geonode.version

    return geonode.version.get_version(__version__)


# PEP 440 compliant version string, referenced by pyproject.toml's dynamic
# version (a plain string attribute, so setuptools doesn't have to stringify the
# __version__ tuple, which would produce an invalid version like "5.1.0.final.0").
__version_str__ = get_version()


def main(_, **settings):
    from django.core.wsgi import get_wsgi_application

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings.get("django_settings"))
    app = get_wsgi_application()
    return app


class GeoNodeException(Exception):
    """Base class for exceptions in this module."""

    pass
