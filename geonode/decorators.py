# -*- coding: utf-8 -*-
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


from functools import wraps

from geonode.utils import check_ogc_backend


def on_ogc_backend(backend_package):
    """Decorator for function specific to a certain ogc backend.

    This decorator will wrap function so it only gets executed if the
    specified ogc backend is currently used. If not, the function will just
    be skipped.

    Useful to decorate features/tests that only available for specific
    backend.
    """

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            on_backend = check_ogc_backend(backend_package)
            if on_backend:
                return func(*args, **kwargs)

        return wrapper

    return decorator
