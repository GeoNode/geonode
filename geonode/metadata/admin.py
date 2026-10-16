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

import logging

from django.contrib import messages
from django.http import HttpResponse
from django.utils.translation.trans_real import get_language_from_request

from geonode.metadata.validation import MetadataValidator
from geonode.metadata.validation.reporting import write_report

logger = logging.getLogger(__name__)

# One admin message per line: report the first few only, and say how many were left out
MAX_REPORTED_RESOURCES = 10
MAX_REPORTED_ERRORS = 5


def validate_metadata(modeladmin, request, queryset):
    """
    Validate the metadata of the selected resources against the metadata jsonschema,
    reporting the outcome as admin messages
    """
    try:
        validator = MetadataValidator(lang=get_language_from_request(request)[:2])
    except ImportError as e:
        modeladmin.message_user(request, str(e), messages.ERROR)
        return

    # Admin messages go through Django's cookie-based message storage, which has a fixed size
    # budget and no session fallback here: an uncapped loop risks losing messages to that limit
    # instead of to this cap. Point at the download action for anything past it.
    for message in validator.schema_errors[:MAX_REPORTED_RESOURCES]:
        modeladmin.message_user(request, message, messages.WARNING)
    if len(validator.schema_errors) > MAX_REPORTED_RESOURCES:
        omitted = len(validator.schema_errors) - MAX_REPORTED_RESOURCES
        modeladmin.message_user(
            request,
            f"... {omitted} more schema problem(s) not shown here: use 'Download validation report' "
            f"for the full list",
            messages.WARNING,
        )

    total = 0
    invalid = []
    for resource in queryset:
        total += 1
        record = validator.validate_resource(resource, max_errors=MAX_REPORTED_ERRORS)
        if not record["valid"]:
            invalid.append(record)

    for record in invalid[:MAX_REPORTED_RESOURCES]:
        modeladmin.message_user(request, describe(record), messages.ERROR)

    # An optional field the schema refuses to leave empty is not the resource's fault: say so
    for field in sorted(validator.observed_defects):
        modeladmin.message_user(
            request,
            f"The metadata schema does not allow the optional field '{field}' to be left empty: "
            f"a problem of the schema itself, not of the selected resources",
            messages.WARNING,
        )

    modeladmin.message_user(request, summarize(total, invalid), messages.ERROR if invalid else messages.SUCCESS)


validate_metadata.short_description = "Validate the metadata"


def download_validation_report(modeladmin, request, queryset):
    """
    Validate the metadata of the selected resources and return the full report as a downloadable
    JSON file: unlike validate_metadata, nothing here is capped for display as admin messages
    """
    try:
        validator = MetadataValidator(lang=get_language_from_request(request)[:2])
    except ImportError as e:
        modeladmin.message_user(request, str(e), messages.ERROR)
        return

    records = [validator.validate_resource(resource) for resource in queryset]
    invalid = [record for record in records if not record["valid"]]

    summary = list(validator.schema_errors)
    for field in sorted(validator.observed_defects):
        summary.append(
            f"The metadata schema does not allow the optional field '{field}' to be left empty: "
            f"a problem of the schema itself, not of the selected resources"
        )
    summary.append(summarize(len(records), invalid, capped=False))

    response = HttpResponse(content_type="application/json")
    response["Content-Disposition"] = 'attachment; filename="metadata_validation_report.json"'
    write_report(summary, records, response, outformat="json")
    return response


download_validation_report.short_description = "Download validation report"


def describe(record):
    """One line per invalid resource: its name, how many errors it has, and the first few of them"""
    details = "; ".join(f"{error['title'] or error['path']}: {error['message']}" for error in record["errors"])
    if record["error_count"] > len(record["errors"]):
        details += f"; ... {record['error_count'] - len(record['errors'])} more"

    return f"'{record['title']}' (id {record['id']}): {record['error_count']} error(s) -- {details}"


def summarize(total, invalid, capped=True):
    if not invalid:
        return f"Validated {total} resource(s): all valid"

    summary = f"Validated {total} resource(s): {len(invalid)} invalid, {total - len(invalid)} valid"
    if capped and len(invalid) > MAX_REPORTED_RESOURCES:
        summary += f" (only the first {MAX_REPORTED_RESOURCES} are listed)"
    return summary
