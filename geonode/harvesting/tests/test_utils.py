##############################################
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
from lxml import etree

from geonode.tests.base import GeoNodeBaseSimpleTestSupport
from geonode.utils import get_xpath_value


class UtilsTestCase(GeoNodeBaseSimpleTestSupport):

    def test_get_xpath_value(self):
        fixtures = [
            (
                "<ns1:myElement xmlns:ns1='fake1' xmlns:ns2='fake2'><ns2:anotherElement>phony</ns2:anotherElement></ns1:myElement>",
                "/ns1:myElement/ns2:anotherElement",
                None,
                "phony"
            ),
            (
                "<ns1:myElement xmlns:ns1='fake1' xmlns:ns2='fake2'><ns2:anotherElement>phony</ns2:anotherElement></ns1:myElement>",
                "ns2:anotherElement",
                None,
                "phony"
            ),
            (
                "<ns1:myElement xmlns:ns1='fake1' xmlns:ns2='fake2' xmlns:ns3='fake3'><ns2:anotherElement><ns3:additional>phony</ns3:additional></ns2:anotherElement></ns1:myElement>",
                "ns2:anotherElement/ns3:additional",
                None,
                "phony"
            ),
        ]
        for element, xpath_expr, nsmap, expected in fixtures:
            xml_el = etree.fromstring(element)
            result = get_xpath_value(xml_el, xpath_expr, nsmap=nsmap)
            self.assertEqual(result, expected)
