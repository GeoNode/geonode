#########################################################################
#
# Copyright (C) 2020 OSGeo
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
from django import db
from djcelery.loaders import DjangoLoader


class GeoNodeCeleryTaksLoader(DjangoLoader):
    def on_task_init(self, task_id, task):
        """Called before every task."""
        for conn in db.connections.all():
            try:
                if not conn.in_atomic_block and \
                    (not conn.connection or
                     (conn.connection.cursor() and not conn.is_usable())):
                    conn.close()
            except Exception:
                pass
        super().on_task_init(task_id, task)
