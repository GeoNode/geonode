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

# from django.utils.timezone import now
# from django.utils.module_loading import import_string
# import jsonschema
from lxml import etree

from . import models


# explicitly disable resolving XML entities in order to prevent malicious attacks
XML_PARSER: typing.Final = etree.XMLParser(resolve_entities=False)


# def update_harvester_availability(
#         harvester: models.Harvester,
#         timeout_seconds: typing.Optional[int] = 5
# ) -> bool:
#     harvester.status = harvester.STATUS_CHECKING_AVAILABILITY
#     harvester.save()
#     worker = harvester.get_harvester_worker()
#     harvester.last_checked_availability = now()
#     available = worker.check_availability(timeout_seconds=timeout_seconds)
#     harvester.remote_available = available
#     harvester.status = harvester.STATUS_READY
#     harvester.save()
#     return available


def initiate_harvesting_refresh_session(harvester: models.Harvester):
    # - check if the harvester is not busy with some other command
    # - set the new harvester status
    # - create a refresh session
    # - call the relevant celery task
    should_continue, error_msg = _should_act(harvester)
    if should_continue:
        harvester.status = harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES
        harvester.save()
        refresh_session = models.HarvestableResourceRefreshSession.objects.create(harvester=harvester)
        tasks.update_harvestable_resources.apply_async(args=(refresh_session.pk,))
        # tasks.update_harvestable_resources.apply_async(args=(harvester.pk,))
        being_updated.append(harvester)
    else:
        self.message_user(request, error_msg, level=messages.ERROR)
        continue
    pass


# def validate_worker_configuration(harvester_type, configuration: typing.Dict):
#     worker_class = import_string(harvester_type)
#     schema = worker_class.get_extra_config_schema()
#     if schema is not None:
#         try:
#             jsonschema.validate(configuration, schema)
#         except jsonschema.exceptions.SchemaError as exc:
#             raise RuntimeError(f"Invalid schema: {exc}")


def get_xpath_value(
        element: etree.Element,
        xpath_expression: str,
        nsmap: typing.Optional[dict] = None
) -> typing.Optional[str]:
    if not nsmap:
        nsmap = element.nsmap
    values = element.xpath(f"{xpath_expression}//text()", namespaces=nsmap)
    return "".join(values).strip() or None
#
#
# def _should_act(
#         harvester: models.Harvester,
#         target_status: typing.Optional[str] = None,
# ) -> typing.Tuple[bool, str]:
#     target_ = target_status or harvester.STATUS_READY
#     if harvester.status != target_:
#         error_message = (
#             f"Harvester {harvester!r} is currently busy. Please wait until its status "
#             f"is {target_!r} before retrying"
#         )
#         result = False
#     else:
#         available = harvester.update_availability()
#         if not available:
#             error_message = (
#                 f"harvester {harvester!r} is not available, skipping...")
#             result = False
#         else:
#             result = True
#             error_message = ""
#     return result, error_message
