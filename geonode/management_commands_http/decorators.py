#########################################################################
#
# Copyright (C) 2021 OSGeo
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
class expose_command_over_http:
    """
    - Add this decorator @expose_command_over_http to the BaseCommand
    (django.core.management.base.BaseCommand) you want to expose over http.
    - It will inject the attribute "expose_command_over_http" that is used to
    determine wherever the Command should be exposed or not.
    """
    def __init__(self, inner_object):
        self.inner_object = inner_object
        self.inner_object.expose_command_over_http = True

    def __call__(self, *args, **kwargs):
        return self.inner_object(*args, **kwargs)
