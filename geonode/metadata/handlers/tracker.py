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
import traceback

from django.conf import settings

from geonode.base.models import ResourceBase
from geonode.metadata.handlers.abstract import MetadataHandler
from geonode.metadata.tracking.operation import (
    CONTEXT_PRE_INSTANCE,
    MetadataOperation,
    current_operation,
    tracking_enabled,
)

logger = logging.getLogger(__name__)

# The operation this save belongs to
CONTEXT_OPERATION = "tracker_operation"

# The callers already known not to declare their operations: one warning each is enough
_undeclared_callers = set()

# Frames to walk past when looking for the caller: they are the machinery, not whoever used it
_INTERNAL_FRAMES = (
    "/geonode/metadata/handlers/",
    "/geonode/metadata/manager.py",
    "/geonode/metadata/tracking/",
)


class TrackerHandler(MetadataHandler):
    """
    Takes the state preceding a metadata change, so that it can be compared with the one following
    it. Handles no field of its own, and has to be called last, so that what it reads is the state
    every other handler has left behind.
    """

    def update_schema(self, jsonschema: dict, context: dict, lang=None):
        return jsonschema

    def get_jsonschema_instance(
        self, resource: ResourceBase, field_name: str, context: dict, errors: dict, lang: str = None
    ):
        pass

    def update_resource(
        self, resource: ResourceBase, field_name: str, json_instance: dict, context: dict, errors: dict, **kwargs
    ):
        pass

    def load_deserialization_context(self, resource: ResourceBase, jsonschema: dict, context: dict):
        """
        Take the state preceding the change, before any handler gets to modify the resource.

        This loop is not guarded by the manager: an error in here would break the save itself,
        so nothing is allowed to escape
        """
        if not tracking_enabled():
            return

        try:
            operation = current_operation() or self._operation_for_an_undeclared_change(resource, context)
            # the caller of this very save may know who is changing the metadata, even when
            # whoever declared the operation did not
            operation.attribute(self._user_of(context))
            operation.snapshot(resource, lambda: self._instance_before(resource, context))
            context[CONTEXT_OPERATION] = operation
        except Exception as e:
            context.pop(CONTEXT_OPERATION, None)
            logger.error(f"Can not read the metadata of resource {resource.pk} before the change", exc_info=e)

    def post_save(self, resource: ResourceBase, json_instance: dict, context: dict, errors: dict, **kwargs):
        """
        A declared operation is recorded when its block ends, since more saves may still be coming.
        An undeclared one is over as soon as its single save is
        """
        operation = context.get(CONTEXT_OPERATION, None)
        if operation is None or current_operation() is not None:
            return

        try:
            operation.close()
        except Exception as e:
            # not through _set_error(): a change that could not be tracked is not a metadata error
            logger.error(f"Can not track the changes of resource {resource.pk}", exc_info=e)

    def _instance_before(self, resource, context):
        """
        The instance the caller has already read, when it passed one along, or a new one.

        Read untranslated: a record of what changed should not depend on the language the editor
        happened to be using
        """
        from geonode.metadata.manager import metadata_manager

        if (supplied := context.get(CONTEXT_PRE_INSTANCE, None)) is not None:
            return supplied

        return metadata_manager.build_schema_instance(resource, lang=None)

    @staticmethod
    def _user_of(context):
        """An anonymous user names nobody: that is not an attribution"""
        user = context.get("user", None)
        return user if getattr(user, "pk", None) is not None else None

    def _operation_for_an_undeclared_change(self, resource, context):
        """
        A caller that did not declare its operation still gets its change recorded, one record per
        save: there is no telling where such an operation ends
        """
        if (user := self._user_of(context)) is not None:
            self._warn_undeclared_caller(resource, f"recorded as a change of its own, by '{user}'")
        else:
            self._warn_undeclared_caller(
                resource, f"recorded under '{getattr(settings, 'METADATA_TRACK_DEFAULTUSER', None)}', not attributed"
            )

        return MetadataOperation(user)

    def _warn_undeclared_caller(self, resource, outcome):
        """Name the caller: a bare warning would leave whoever reads it hunting for it"""
        caller = "unknown"
        for frame in reversed(traceback.extract_stack()):
            if not any(internal in frame.filename for internal in _INTERNAL_FRAMES):
                caller = f"{frame.filename}:{frame.lineno}"
                break

        if caller in _undeclared_callers:
            return

        _undeclared_callers.add(caller)
        logger.warning(
            f"Metadata of resource {resource.pk} changed outside of a metadata_tracker() block, "
            f"from {caller}: {outcome}"
        )
