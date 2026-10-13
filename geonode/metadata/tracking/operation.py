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
Boundaries of a metadata change.

A caller about to change some metadata declares the operation and who requested it:

    with metadata_tracker(user):
        resource_manager.update(...)

Whatever happens inside, however many saves it takes, is a single change performed by that user.
Nested blocks join the outer one, so the internal sequences are not exposed as separate changes.
"""

import logging
from contextlib import contextmanager
from contextvars import ContextVar

from django.conf import settings

from geonode.metadata.tracking.delta import compute_delta

activity = None
if "actstream" in settings.INSTALLED_APPS:
    from actstream import action as activity

logger = logging.getLogger(__name__)

# Context key holding the instance preceding the change, when the caller has already read it
CONTEXT_PRE_INSTANCE = "pre_instance"

# The operation being performed, if any. A ContextVar and not a thread local: asgiref carries it
# across the sync/async boundaries, a thread local would not survive them
_current_operation = ContextVar("metadata_tracker_operation", default=None)


def tracking_enabled():
    """Read when called, so that the setting can be overridden at runtime"""
    return getattr(settings, "METADATA_TRACK_CHANGES", False)


def current_operation():
    """The operation being performed, None when the caller did not declare any"""
    return _current_operation.get()


class MetadataOperation:
    """
    One metadata change, as the caller means it: the state preceding it is taken once per resource,
    however many saves the operation needs
    """

    def __init__(self, user=None):
        self.user = user
        self.snapshots = {}

    def attribute(self, user):
        """
        Name the user performing the change, when the caller declared the operation without
        knowing it yet. The first one named wins: an operation is one user's doing
        """
        if self.user is None and user is not None:
            self.user = user

    def snapshot(self, resource, build_instance):
        """Keep the state preceding the operation. Only the first call for a resource counts"""
        if resource.pk in self.snapshots:
            return
        self.snapshots[resource.pk] = (resource, build_instance())

    def close(self):
        try:
            # an operation nobody claimed is recorded under the default user, marked as not theirs
            user, attributed = (self.user, True) if self.user is not None else (default_user(), False)
        except Exception as e:
            # the change did happen: failing to record it is not a reason to fail the caller too
            logger.error("Can not tell who to record the metadata changes under", exc_info=e)
            return

        for resource, before in self.snapshots.values():
            try:
                track_change(resource, before, user, attributed)
            except Exception as e:
                logger.error(f"Can not track the changes of resource {resource.pk}", exc_info=e)


def read_instance(resource):
    """
    The metadata of a resource as it stands. Always untranslated: a record of what changed should
    not depend on the language whoever was editing happened to be using
    """
    from geonode.metadata.manager import metadata_manager

    return metadata_manager.build_schema_instance(resource, lang=None)


def _snapshot_now(operation, resource):
    """Nothing of the tracking is allowed to break the change being tracked"""
    if resource is None:
        return
    try:
        operation.snapshot(resource, lambda: read_instance(resource))
    except Exception as e:
        logger.error(f"Can not read the metadata of resource {resource.pk} before the change", exc_info=e)


def default_user():
    """The user the changes nobody claimed are recorded under"""
    from django.contrib.auth import get_user_model

    username = getattr(settings, "METADATA_TRACK_DEFAULTUSER", None)
    user = get_user_model().objects.filter(username=username).first()
    if user is None:
        raise ValueError(f"METADATA_TRACK_DEFAULTUSER names no existing user: '{username}'")
    return user


@contextmanager
def metadata_tracker(user, resource=None):
    """
    Declare a metadata change on behalf of `user`. Nested blocks join the outer one.

    `user` is to be passed explicitly, None included: a caller that does not know who is changing
    the metadata still groups its saves into one change, which is then attributed by whatever does
    know, or recorded under the default user.

    `resource` is to be passed whenever it is known already: the state preceding the change is
    read when the block is entered, and not when the first metadata save happens, so that whatever
    the caller writes to the resource in between is part of the change and not of its premises
    """
    if not tracking_enabled():
        yield None
        return

    if (running := current_operation()) is not None:
        # an inner block is part of the operation already being performed, not another one.
        # It may well know the user, or the resource, the outer one was opened without
        running.attribute(user)
        _snapshot_now(running, resource)
        yield running
        return

    operation = MetadataOperation(user)
    _snapshot_now(operation, resource)
    token = _current_operation.set(operation)
    try:
        yield operation
        # not reached when the block raises: nothing was changed, and a partial difference misleads
        operation.close()
    finally:
        # by token, so that a block left by an unusual path does not leak into the next operation
        _current_operation.reset(token)


def track_change(resource, before, user, attributed=True):
    """
    Compare the current state of the resource with the one preceding the change, and record it.

    Reading the state again is the expensive part, hence it being done once the operation is over
    """
    # To be read here and not later on: a save coming next would be read as part of this change
    resource.refresh_from_db()
    after = read_instance(resource)

    if delta := compute_delta(before, after):
        store_change(resource, delta, user, attributed)
    else:
        logger.debug(f"No metadata change to record for resource {resource.pk}")


def store_change(resource, delta, user, attributed=True):
    """
    Hand the change over to whoever stores it. `attributed` tells whether the user really
    requested the change, or is just who it is recorded under.

    Deliberately synchronous: what is left to do by now is a single insert, and handing it over to
    a task would cost more than it saves, besides losing the change whenever the worker is not
    there to take it. Worth revisiting if this ever grows some I/O of its own
    """
    logger.info(
        f"Metadata of resource {resource.pk} changed by {user}"
        f"{'' if attributed else ' (not attributed)'}: {dict(sorted(delta.items()))}"
    )
    if activity:
        activity.send(
            user,
            verb="updated metadata",
            action_object=resource,
            raw_action="updated metadata",
            data={
                "changes": delta,
            },
        )
