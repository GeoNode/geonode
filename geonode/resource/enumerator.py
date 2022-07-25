#########################################################################
#
# Copyright (C) 2022 OSGeo
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
import enum
from django.utils.translation import gettext_lazy as _


class ExecutionRequestAction(enum.Enum):
    upload = _("upload")  # import will be better, but it will clash with the python import statement
    create = _("create")
    copy = _("copy")
    delete = _("delete")
    permissions = _("permissions")
    update = _("update")
    ingest = _("ingest")
    unknown = _("unknown")
