#########################################################################
#
# Copyright (C) 2026 OSGeo
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
from requests.auth import HTTPBasicAuth

from geonode.sources.auth import FormAuthHandler


class WmsAuthHandler(FormAuthHandler):
    """Connection parameters of an OGC WMS, the type matches the source provider key"""

    handled_type = "wms"

    def _init_from_config(self):
        payload = self.config.payload
        self.url = payload.get("url")
        self.version = payload.get("version")
        self.username = payload.get("username")
        self.password = payload.get("password")

    def get_request_auth(self):
        # a public service has no credentials, requests then sends no Authorization header
        return HTTPBasicAuth(self.username, self.password) if self.username else None

    def get_credentials(self):
        return (self.username, self.password)
