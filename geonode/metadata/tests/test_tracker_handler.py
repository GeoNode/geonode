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

from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, override_settings

from geonode.base.models import ResourceBase
from geonode.metadata.handlers import tracker as tracker_handler
from geonode.metadata.handlers.tracker import CONTEXT_OPERATION, TrackerHandler
from geonode.metadata.manager import metadata_manager
from geonode.metadata.tracking.operation import CONTEXT_PRE_INSTANCE, metadata_tracker


@override_settings(METADATA_TRACK_CHANGES=True, METADATA_TRACK_DEFAULTUSER="tracker_default")
class TrackerHandlerTests(TestCase):
    """
    What the handler does around a save: it is the part making sure no change goes unrecorded,
    whether the caller declared its operation or not
    """

    def setUp(self):
        self.handler = TrackerHandler()
        self.user = get_user_model().objects.create_user("tracker_user", "u@fakemail.com", "pwd")
        self.default_user = get_user_model().objects.create_user("tracker_default", "d@fakemail.com", "pwd")
        self.resource = ResourceBase.objects.create(title="Tracked", uuid=str(uuid4()), owner=self.user)

        # the callers already warned about are remembered process-wide
        tracker_handler._undeclared_callers.clear()
        self.addCleanup(tracker_handler._undeclared_callers.clear)

        patcher = patch("geonode.metadata.tracking.operation.store_change")
        self.store_change = patcher.start()
        self.addCleanup(patcher.stop)

    def load_context(self, context=None):
        context = {} if context is None else context
        self.handler.load_deserialization_context(self.resource, {}, context)
        return context

    def changing(self, before={"title": "before"}, after={"title": "after"}):
        """The metadata is read twice: the state preceding the change, then the one following it"""
        return patch.object(metadata_manager, "build_schema_instance", side_effect=[before, after])

    # -- the state preceding the change ------------------------------------------------

    def test_the_instance_the_caller_already_read_is_not_read_again(self):
        supplied = {"title": "handed over"}

        with patch.object(metadata_manager, "build_schema_instance") as build:
            context = self.load_context({CONTEXT_PRE_INSTANCE: supplied})

        build.assert_not_called()
        self.assertEqual({self.resource.pk: (self.resource, supplied)}, context[CONTEXT_OPERATION].snapshots)

    def test_the_state_is_read_untranslated(self):
        # a record of what changed should not depend on the language the editor was using
        with patch.object(metadata_manager, "build_schema_instance", return_value={}) as build:
            self.load_context({"lang": "it"})

        self.assertIsNone(build.call_args.kwargs["lang"])

    def test_nothing_is_read_while_the_tracking_is_disabled(self):
        with override_settings(METADATA_TRACK_CHANGES=False):
            with patch.object(metadata_manager, "build_schema_instance") as build:
                context = self.load_context()

        build.assert_not_called()
        self.assertNotIn(CONTEXT_OPERATION, context)

    def test_a_failure_while_reading_does_not_break_the_save(self):
        # this hook is not guarded by the manager: an error escaping it would abort the request
        with patch.object(metadata_manager, "build_schema_instance", side_effect=RuntimeError("boom")):
            context = self.load_context()

        self.assertNotIn(CONTEXT_OPERATION, context)

    # -- when the change gets recorded -------------------------------------------------

    def test_an_undeclared_change_is_recorded_as_soon_as_its_save_is_over(self):
        with self.changing():
            context = self.load_context()
            self.handler.post_save(self.resource, {}, context, {})

        self.store_change.assert_called_once()
        self.assertEqual(self.resource.pk, self.store_change.call_args.args[0].pk)
        self.assertEqual({"title": {"from": "before", "to": "after"}}, self.store_change.call_args.args[1])

    def test_a_declared_change_is_not_recorded_before_its_block_ends(self):
        with self.changing():
            with metadata_tracker(self.user):
                context = self.load_context()
                self.handler.post_save(self.resource, {}, context, {})
                self.store_change.assert_not_called()  # the operation is not over yet

        self.store_change.assert_called_once()

    def test_several_saves_of_one_operation_make_a_single_record(self):
        with self.changing():
            with metadata_tracker(self.user):
                for _ in range(3):
                    context = self.load_context()
                    self.handler.post_save(self.resource, {}, context, {})

        self.store_change.assert_called_once()

    def test_a_change_without_differences_is_not_recorded(self):
        with patch.object(metadata_manager, "build_schema_instance", return_value={"title": "same"}):
            context = self.load_context()
            self.handler.post_save(self.resource, {}, context, {})

        self.store_change.assert_not_called()

    # -- who the change is recorded under ----------------------------------------------

    def test_a_declared_change_carries_the_user_who_requested_it(self):
        with self.changing():
            with metadata_tracker(self.user):
                self.load_context()

        self.assertEqual(self.user, self.store_change.call_args.args[2])
        self.assertTrue(self.store_change.call_args.args[3])

    def test_an_undeclared_change_is_recorded_under_the_default_user_and_marked(self):
        with self.changing():
            context = self.load_context()
            self.handler.post_save(self.resource, {}, context, {})

        self.assertEqual(self.default_user, self.store_change.call_args.args[2])
        self.assertFalse(self.store_change.call_args.args[3], "an undeclared change must not look attributed")

    def test_a_caller_naming_the_user_is_believed_even_without_a_block(self):
        # resource_manager.create() knows the owner: it just does not declare the operation
        with self.changing():
            context = self.load_context({"user": self.user})
            self.handler.post_save(self.resource, {}, context, {})

        self.assertEqual(self.user, self.store_change.call_args.args[2])
        self.assertTrue(self.store_change.call_args.args[3], "the caller told us who: that is an attribution")

    def test_an_anonymous_user_is_not_an_attribution(self):
        with self.changing():
            context = self.load_context({"user": AnonymousUser()})
            self.handler.post_save(self.resource, {}, context, {})

        self.assertEqual(self.default_user, self.store_change.call_args.args[2])
        self.assertFalse(self.store_change.call_args.args[3])

    def test_an_undeclared_change_names_its_caller_once(self):
        with patch.object(metadata_manager, "build_schema_instance", return_value={}):
            with self.assertLogs(tracker_handler.logger, level="WARNING") as logged:
                self.load_context()
                self.load_context()  # the same caller: already warned about

        self.assertEqual(1, len(logged.output))
        self.assertIn("outside of a metadata_tracker() block", logged.output[0])
        self.assertIn(__file__, logged.output[0], "the warning should name the caller")

    def test_an_unknown_default_user_is_not_silently_ignored(self):
        # the default user is only needed once the change is being recorded, not while reading it
        with override_settings(METADATA_TRACK_DEFAULTUSER="no_such_user"):
            with self.changing():
                context = self.load_context()
                with self.assertLogs(tracker_handler.logger, level="ERROR") as logged:
                    self.handler.post_save(self.resource, {}, context, {})

        self.store_change.assert_not_called()
        self.assertTrue([line for line in logged.output if "METADATA_TRACK_DEFAULTUSER" in line])

    def test_a_block_declared_without_a_user_is_attributed_by_the_save(self):
        # resource_manager.update() groups the saves, the save itself may name the user
        with self.changing():
            with metadata_tracker(None):
                context = self.load_context({"user": self.user})
                self.handler.post_save(self.resource, {}, context, {})

        self.assertEqual(self.user, self.store_change.call_args.args[2])
        self.assertTrue(self.store_change.call_args.args[3])
