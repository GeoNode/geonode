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

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from geonode.metadata.tracking.delta import compute_delta
from geonode.metadata.tracking.operation import current_operation, metadata_tracker

BIOTA = {"id": "biota", "label": "Biota"}
FARMING = {"id": "farming", "label": "Farming"}


class ComputeDeltaTests(SimpleTestCase):
    """What changed between two schema instances, labels and ordering aside"""

    def test_nothing_changed(self):
        self.assertEqual({}, compute_delta({"title": "a"}, {"title": "a"}))

    def test_a_changed_value_is_reported_from_and_to(self):
        self.assertEqual({"title": {"from": "a", "to": "b"}}, compute_delta({"title": "a"}, {"title": "b"}))

    def test_a_field_that_was_not_there_has_no_from(self):
        self.assertEqual({"title": {"to": "b"}}, compute_delta({}, {"title": "b"}))

    def test_a_field_no_longer_there_has_no_to(self):
        self.assertEqual({"title": {"from": "a"}}, compute_delta({"title": "a"}, {}))

    def test_an_empty_field_is_not_a_missing_one(self):
        # the handlers leave out what is unset, and hand over a null for what is set to nothing
        self.assertEqual({"x": {"to": None}}, compute_delta({}, {"x": None}))
        self.assertEqual({"x": {"from": None}}, compute_delta({"x": None}, {}))

    def test_a_translated_label_is_not_a_change(self):
        self.assertEqual({}, compute_delta({"category": BIOTA}, {"category": {"id": "biota", "label": "Biota (it)"}}))

    def test_a_different_id_is_a_change(self):
        self.assertEqual(
            {"category": {"from": BIOTA, "to": FARMING}},
            compute_delta({"category": BIOTA}, {"category": FARMING}),
        )

    def test_clearing_an_object_is_a_change(self):
        self.assertEqual(
            {"category": {"from": BIOTA, "to": None}}, compute_delta({"category": BIOTA}, {"category": None})
        )

    def test_lists_are_reported_as_added_and_removed(self):
        self.assertEqual(
            {"regions": {"added": [FARMING], "removed": [BIOTA]}},
            compute_delta({"regions": [BIOTA]}, {"regions": [FARMING]}),
        )

    def test_a_reordered_list_is_not_a_change(self):
        self.assertEqual({}, compute_delta({"k": ["a", "b"]}, {"k": ["b", "a"]}))

    def test_only_the_thesaurus_that_changed_is_reported(self):
        before = {"tkeywords": {"gemet": [BIOTA], "scope": [FARMING]}}
        after = {"tkeywords": {"gemet": [BIOTA, FARMING], "scope": [FARMING]}}

        self.assertEqual({"tkeywords": {"gemet": {"added": [FARMING]}}}, compute_delta(before, after))

    def test_only_the_contact_role_that_changed_is_reported(self):
        before = {"contacts": {"owner": [{"id": "1", "label": "ann"}], "poc": [{"id": "9", "label": "zoe"}]}}
        after = {"contacts": {"owner": [{"id": "2", "label": "bob"}], "poc": [{"id": "9", "label": "zoe"}]}}

        self.assertEqual(
            {"contacts": {"owner": {"added": [{"id": "2", "label": "bob"}], "removed": [{"id": "1", "label": "ann"}]}}},
            compute_delta(before, after),
        )


@override_settings(METADATA_TRACK_CHANGES=True)
class MetadataTrackerTests(SimpleTestCase):
    """The boundaries of a change, as the caller declares them"""

    USER = SimpleNamespace(username="ann")

    def setUp(self):
        patcher = patch("geonode.metadata.tracking.operation.track_change")
        self.track_change = patcher.start()
        self.addCleanup(patcher.stop)

    def resource(self, pk):
        return SimpleNamespace(pk=pk)

    def test_a_nested_block_joins_the_one_already_running(self):
        with metadata_tracker(self.USER) as outer:
            with metadata_tracker(self.USER) as inner:
                self.assertIs(outer, inner)
            self.assertIs(outer, current_operation())

        self.assertIsNone(current_operation())

    def test_the_state_preceding_the_change_is_read_once_per_resource(self):
        reads = []

        with metadata_tracker(self.USER) as operation:
            for _ in range(3):
                operation.snapshot(self.resource(7), lambda: reads.append(1) or {"title": "before"})

        self.assertEqual(1, len(reads))
        self.assertEqual(1, self.track_change.call_count)

    def test_an_operation_can_span_several_resources(self):
        with metadata_tracker(self.USER) as operation:
            operation.snapshot(self.resource(1), dict)
            operation.snapshot(self.resource(2), dict)

        self.assertEqual([1, 2], sorted(call.args[0].pk for call in self.track_change.call_args_list))

    def test_a_failed_operation_records_nothing_and_still_releases_the_scope(self):
        with self.assertRaises(RuntimeError):
            with metadata_tracker(self.USER) as operation:
                operation.snapshot(self.resource(9), dict)
                raise RuntimeError("the save blew up")

        self.track_change.assert_not_called()
        self.assertIsNone(current_operation())

    def test_an_operation_may_be_declared_before_knowing_the_user(self):
        # resource_manager.update() groups its saves without knowing who asked for the change
        with metadata_tracker(None) as operation:
            self.assertIsNone(operation.user)
            operation.attribute(self.USER)
            operation.snapshot(self.resource(4), dict)

        self.assertEqual(self.USER, self.track_change.call_args.args[2])
        self.assertTrue(self.track_change.call_args.args[3])

    def test_the_resource_given_is_read_when_the_block_is_entered(self):
        # resource_manager.update() writes to the resource before the first metadata save: taking
        # the state later would make those writes look like they were there all along
        with patch("geonode.metadata.tracking.operation.read_instance", return_value={"title": "before"}) as read:
            with metadata_tracker(self.USER, resource=self.resource(10)) as operation:
                read.assert_called_once()
                # a later snapshot of the same resource does not replace it
                operation.snapshot(self.resource(10), lambda: {"title": "too late"})

        self.assertEqual({"title": "before"}, self.track_change.call_args.args[1])

    def test_a_block_entered_without_a_resource_reads_nothing(self):
        with patch("geonode.metadata.tracking.operation.read_instance") as read:
            with metadata_tracker(self.USER):
                pass

        read.assert_not_called()

    def test_a_nested_block_names_the_user_the_outer_one_did_not_know(self):
        # resource_manager.update() groups the saves, an inner block may know who asked for them
        with metadata_tracker(None) as outer:
            with metadata_tracker(self.USER) as inner:
                self.assertIs(outer, inner)
            outer.snapshot(self.resource(8), dict)

        self.assertEqual(self.USER, self.track_change.call_args.args[2])
        self.assertTrue(self.track_change.call_args.args[3], "the inner block named the user: that is an attribution")

    def test_the_first_user_named_is_the_one_it_is_recorded_under(self):
        # an operation is one user's doing: a later save does not reassign it
        with metadata_tracker(self.USER) as operation:
            operation.attribute(SimpleNamespace(username="bob"))
            operation.snapshot(self.resource(5), dict)

        self.assertEqual(self.USER, self.track_change.call_args.args[2])

    def test_an_operation_nobody_claimed_falls_back_to_the_default_user(self):
        with patch("geonode.metadata.tracking.operation.default_user", return_value="the-default") as default:
            with metadata_tracker(None) as operation:
                operation.snapshot(self.resource(6), dict)

        default.assert_called_once()
        self.assertEqual("the-default", self.track_change.call_args.args[2])
        self.assertFalse(self.track_change.call_args.args[3], "nobody claimed it: that is not an attribution")

    def test_an_unknown_default_user_does_not_break_the_change_being_tracked(self):
        # METADATA_TRACK_DEFAULTUSER naming nobody is a misconfiguration of the auditing: the
        # change did happen, and failing to record it is not a reason to fail the caller too
        with patch("geonode.metadata.tracking.operation.logger") as logged:
            with patch(
                "geonode.metadata.tracking.operation.default_user", side_effect=ValueError("names no existing user")
            ):
                with metadata_tracker(None) as operation:
                    operation.snapshot(self.resource(11), dict)

        self.track_change.assert_not_called()
        self.assertEqual(1, logged.error.call_count, "a change that went unrecorded is to be reported")
        self.assertIsNone(current_operation(), "the scope is released all the same")

    def test_a_declared_change_is_attributed(self):
        with metadata_tracker(self.USER) as operation:
            operation.snapshot(self.resource(3), dict)

        self.assertTrue(self.track_change.call_args.args[3])

    @override_settings(METADATA_TRACK_CHANGES=False)
    def test_nothing_happens_while_the_tracking_is_disabled(self):
        with metadata_tracker(None) as operation:
            self.assertIsNone(operation)
            self.assertIsNone(current_operation())

        self.track_change.assert_not_called()
