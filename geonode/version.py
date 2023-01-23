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
import datetime
import subprocess


def get_version(version=None):
    "Returns a PEP 440 compliant version number from VERSION."
    if version is None or not isinstance(version, list):
        from geonode import __version__ as version
    else:
        assert len(version) == 5
        assert version[3] in ("final", "rc", "post", "dev")

    # [N!]N(.N)*[{a|b|rc}N][.postN][.devN]
    # Epoch segment: N!
    # Release segment: N(.N)*
    # Pre-release segment: {a|b|rc}N
    # Post-release segment: .postN
    # Development release segment: .devN
    main = ".".join(str(x) for x in version[:3])
    sub = version[3]
    sub_version = str(version[4])
    if sub == "rc":
        sub += sub_version
    elif sub in ["post", "dev"]:
        sub = f".{sub}{sub_version}"
    else:
        sub = ""
    return main + sub


def version(request, version=None):
    from django.http import HttpResponse
    from django.utils.html import escape

    _v = get_version(version=version)
    return HttpResponse(escape(_v))


def get_git_changeset():
    """Returns a numeric identifier of the latest git changeset.

    The result is the UTC timestamp of the changeset in YYYYMMDDHHMMSS format.
    This value isn't guaranteed to be unique, but collisions are very unlikely,
    so it's sufficient for generating the development version numbers.
    """
    try:
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        git_show = subprocess.Popen(
            "git show --pretty=format:%ct --quiet HEAD",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=repo_dir,
            universal_newlines=True,
        )
        timestamp = git_show.communicate()[0].partition("\n")[0]
        return timestamp
    except Exception:
        try:
            timestamp = datetime.datetime.utcfromtimestamp(int(timestamp))
            return timestamp.strftime("%Y%m%d%H%M%S")
        except ValueError:
            return None
