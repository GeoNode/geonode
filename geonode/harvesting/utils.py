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

import typing

from lxml import etree


# explicitly disable resolving XML entities in order to prevent malicious attacks
XML_PARSER: typing.Final = etree.XMLParser(resolve_entities=False)


def get_xpath_value(
        element: etree.Element,
        xpath_expression: str,
        nsmap: typing.Optional[dict] = None
) -> typing.Optional[str]:
    if not nsmap:
        nsmap = element.nsmap
    values = element.xpath(f"{xpath_expression}//text()", namespaces=nsmap)
    return "".join(values).strip() or None
