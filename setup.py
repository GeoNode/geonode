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
from setuptools import setup

import os
import sys

current_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_directory)


setup(
    version=__import__("geonode").get_version(),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    package_data={
        "": ["*.*"],  # noqa
        "": ["static/*.*"],  # noqa
        "static": ["*.*"],
        "": ["templates/*.*"],  # noqa
        "templates": ["*.*"],
    },
)
