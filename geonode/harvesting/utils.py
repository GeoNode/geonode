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
import jsonschema

from lxml import etree

from django.utils.timezone import now
from django.utils.module_loading import import_string

# explicitly disable resolving XML entities in order to prevent malicious attacks
XML_PARSER: typing.Final = etree.XMLParser(resolve_entities=False)


def update_harvester_availability(
        harvester: "Harvester",  # noqa
        timeout_seconds: typing.Optional[int] = 5
) -> bool:
    harvester.status = harvester.STATUS_CHECKING_AVAILABILITY
    harvester.save()
    worker = harvester.get_harvester_worker()
    harvester.last_checked_availability = now()
    available = worker.check_availability(timeout_seconds=timeout_seconds)
    harvester.remote_available = available
    harvester.status = harvester.STATUS_READY
    harvester.save()
    return available


def validate_worker_configuration(harvester_type, configuration: typing.Dict):
    worker_class = import_string(harvester_type)
    schema = worker_class.get_extra_config_schema()
    if schema is not None:
        try:
            jsonschema.validate(configuration, schema)
        except jsonschema.exceptions.SchemaError as exc:
            raise RuntimeError(f"Invalid schema: {exc}")


def get_xpath_value(
        element: etree.Element,
        xpath_expression: str,
        nsmap: typing.Optional[dict] = None
) -> typing.Optional[str]:
    if not nsmap:
        nsmap = element.nsmap
    values = element.xpath(f"{xpath_expression}//text()", namespaces=nsmap)
    return "".join(values).strip() or None
