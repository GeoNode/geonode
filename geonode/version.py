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

import datetime
import os
import subprocess


def get_version(version=None):
    "Returns a PEP 386-compliant version number from VERSION."
    if version is None or not isinstance(version, list):
        from geonode import __version__ as version
    else:
        assert len(version) == 5
        assert version[3] in ('unstable', 'beta', 'rc', 'final')

    # Now build the two parts of the version number:
    # main = X.Y[.Z]
    # sub = .devN - for pre-alpha releases
    #     | {a|b|c}N - for alpha, beta and rc releases
    git_changeset = get_git_changeset()
    main = '.'.join(str(x) for x in version[:3])
    sub = ''
    if version[3] not in ('unstable', 'final'):
        mapping = {'beta': 'b', 'rc': 'rc'}
        sub = mapping[version[3]] + str(version[4])
    if git_changeset:
        if version[3] == 'unstable':
            sub += f'.dev{git_changeset}'
        elif version[3] != 'final':
            sub += f'.build{git_changeset}'
    return main + sub


def version(request, version=None):
    from django.http import HttpResponse
    _v = get_version(version=version)
    return HttpResponse(_v)


def get_git_changeset():
    """Returns a numeric identifier of the latest git changeset.

    The result is the UTC timestamp of the changeset in YYYYMMDDHHMMSS format.
    This value isn't guaranteed to be unique, but collisions are very unlikely,
    so it's sufficient for generating the development version numbers.
    """
    try:
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        git_show = subprocess.Popen('git show --pretty=format:%ct --quiet HEAD',
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    shell=True, cwd=repo_dir, universal_newlines=True)
        timestamp = git_show.communicate()[0].partition('\n')[0]
        return timestamp
    except Exception:
        try:
            timestamp = datetime.datetime.utcfromtimestamp(int(timestamp))
            return timestamp.strftime('%Y%m%d%H%M%S')
        except ValueError:
            return None
