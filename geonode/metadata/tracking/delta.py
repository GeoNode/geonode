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

"""
Comparison of two schema instances.

The result only contains what changed, and is made of plain JSON types, so that it can be stored
along the activity stream action:

    {
        "title": {"from": "Old title", "to": "New title"},
        "tkeywords": {
            "gemet-inspire-themes": {"added": [{"id": "...", "label": "Biota"}]}
        },
    }

- a missing "from" means the field was not in the instance at all, which is not the same as being
  there with a null value;
- entries carrying both an "id" and a "label" are compared by id alone: labels are localized, and a
  change of language is not a change of metadata;
- lists are reported as added/removed entries, a reordering is not a change.
"""

import json

# Not a value a handler can produce, so it can tell "no such field" from "field set to null"
ABSENT = object()


def compute_delta(before: dict, after: dict) -> dict:
    """Return what changed between the two schema instances, empty dict if nothing did"""
    return _diff_mapping(before or {}, after or {})


def _is_identified(value):
    """An entry standing for a db object: the id is what identifies it, the label just names it"""
    return isinstance(value, dict) and "id" in value and "label" in value


def _identity(value):
    """What makes two values the same one, labels and ordering aside"""
    if _is_identified(value):
        return "id", value["id"]
    if isinstance(value, (dict, list)):
        return "json", json.dumps(value, sort_keys=True, default=str)
    return "value", value


def _diff_mapping(before, after):
    delta = {}
    for field in before.keys() | after.keys():
        if (change := _diff_value(before.get(field, ABSENT), after.get(field, ABSENT))) is not None:
            delta[field] = change
    return delta


def _diff_value(before, after):
    if isinstance(before, dict) and isinstance(after, dict) and not (_is_identified(before) or _is_identified(after)):
        # a plain object (tkeywords, contacts...): tell which of its entries changed, not the lot
        return _diff_mapping(before, after) or None

    if isinstance(before, list) and isinstance(after, list):
        return _diff_list(before, after)

    if _identity(before) == _identity(after):
        return None

    return {key: value for key, value in (("from", before), ("to", after)) if value is not ABSENT}


def _diff_list(before, after):
    before_items = {_identity(item): item for item in before}
    after_items = {_identity(item): item for item in after}

    change = {
        "added": [item for identity, item in after_items.items() if identity not in before_items],
        "removed": [item for identity, item in before_items.items() if identity not in after_items],
    }
    change = {key: items for key, items in change.items() if items}
    return change or None
