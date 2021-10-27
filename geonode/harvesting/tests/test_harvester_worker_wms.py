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
from geonode.harvesting.harvesters import wms
from geonode.tests.base import GeoNodeBaseSimpleTestSupport


class WmsModuleTestCase(GeoNodeBaseSimpleTestSupport):

    def test_get_nsmap(self):
        fixtures = [
            ({None: "ns1uri", "ns2": "ns2uri"}, {"wms": "ns1uri", "ns2": "ns2uri"}),
            ({"ns1": "ns1uri", "ns2": "ns2uri"}, {"ns1": "ns1uri", "ns2": "ns2uri"}),
        ]
        for original, expected in fixtures:
            result = wms._get_nsmap(original)
            self.assertEqual(result, expected)
