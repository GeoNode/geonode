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

import csv
import json

BASE_FIELDS = ["id", "uuid", "resource_type", "title", "valid", "error_count"]
ERROR_FIELDS = ["error_path", "error_title", "error_validator", "error_message", "error_value"]


def write_report(summary, records, out, outformat="json", error_details=True):
    """
    Write a MetadataValidator report (the summary lines plus the per-resource records) to `out`,
    in the given format. `out` only needs a `write(str)` method: an open file, Django's stdout
    wrapper, an HttpResponse, ...
    """
    if not error_details:
        records = [{k: v for k, v in record.items() if k != "errors"} for record in records]

    if outformat == "json":
        json.dump({"summary": summary, "resources": records}, out, indent=2, ensure_ascii=False, default=str)
        out.write("\n")
    else:
        # CSV has no comment syntax: "#" is only a widespread convention
        for message in summary:
            out.write(f"# {message}\n")
        write_csv(records, out, error_details)


def write_csv(records, out, error_details):
    fields = BASE_FIELDS + (ERROR_FIELDS if error_details else [])
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()

    for record in records:
        if not error_details or not record["errors"]:
            writer.writerow(record)
            continue

        # one row per error, the resource columns are repeated
        for error in record["errors"]:
            writer.writerow(
                dict(
                    record,
                    error_path=error["path"],
                    error_title=error["title"],
                    error_validator=error["validator"],
                    error_message=error["message"],
                    error_value=error["value"],
                )
            )
