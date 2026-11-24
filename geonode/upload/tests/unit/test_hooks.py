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
from unittest.mock import MagicMock, patch

from django.test import override_settings

from geonode.resource.models import ExecutionRequest
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.upload.handlers.geojson.handler import GeoJsonFileHandler
from geonode.upload.hooks import BaseImporterSubscriber, ImporterHooks

HANDLER_PATH = "geonode.upload.handlers.geojson.handler.GeoJsonFileHandler"
SUBSCRIBER_PATH = "geonode.upload.tests.unit.test_hooks.DummySubscriber"
subscriber_callback = MagicMock()


def execution(action="upload", handler_module_path=HANDLER_PATH):
    return ExecutionRequest(action=action, input_params={"handler_module_path": handler_module_path})


class DummySubscriber(BaseImporterSubscriber):
    def register(self, hooks):
        hooks.add_action("upload.completed", subscriber_callback)


class TestImporterHooks(GeoNodeBaseTestSupport):
    def setUp(self):
        self.sut = ImporterHooks()

    def test_add_action_should_raise_if_phase_is_unknown(self):
        """An unknown phase is a configuration error and must fail at registration"""
        with self.assertRaises(ValueError):
            self.sut.add_action("upload.finished", MagicMock())

    def test_add_action_should_raise_if_action_is_missing(self):
        """An event without the action part must fail at registration"""
        with self.assertRaises(ValueError):
            self.sut.add_action("completed", MagicMock())

    def test_add_action_should_accept_custom_actions(self):
        """Out-of-tree handlers can define their own actions"""
        _callback = MagicMock()
        self.sut.add_action("my_custom_action.completed", _callback)
        _exec = execution(action="my_custom_action")

        self.sut.do_action("completed", _exec)

        _callback.assert_called_once()

    def test_do_action_should_call_the_callbacks_matching_the_event(self):
        """Exact and wildcard events must match, events of other actions must not"""
        _exact, _any_action, _any_phase, _any, _other = (MagicMock() for _ in range(5))
        self.sut.add_action("upload.completed", _exact)
        self.sut.add_action("*.completed", _any_action)
        self.sut.add_action("upload.*", _any_phase)
        self.sut.add_action("*.*", _any)
        self.sut.add_action("replace.completed", _other)
        _exec = execution()

        self.sut.do_action("completed", _exec)

        for _callback in (_exact, _any_action, _any_phase, _any):
            _callback.assert_called_once()
        _other.assert_not_called()

    def test_do_action_should_pass_execution_handler_and_kwargs(self):
        """The callback must receive the execution, the handler class and the event kwargs"""
        _callback = MagicMock()
        self.sut.add_action("upload.failed", _callback)
        _exec = execution()

        self.sut.do_action("failed", _exec, reason="boom")

        _callback.assert_called_once()
        args, kwargs = _callback.call_args
        self.assertEqual(_exec, args[0])
        self.assertEqual(GeoJsonFileHandler, args[1])
        self.assertDictEqual({"reason": "boom"}, kwargs)

    def test_do_action_should_pass_none_if_handler_is_not_available(self):
        """A missing or not importable handler must not prevent the callbacks from running"""
        _callback = MagicMock()
        self.sut.add_action("upload.completed", _callback)

        with self.assertLogs("importer", level="WARNING"):
            self.sut.do_action(
                "completed", execution(handler_module_path="geonode.upload.handlers.not_existing.Handler")
            )
        self.sut.do_action("completed", execution(handler_module_path=None))

        self.assertListEqual([None, None], [call.args[1] for call in _callback.call_args_list])

    @patch("geonode.upload.hooks.import_string")
    def test_do_action_should_not_load_the_handler_if_no_callback_matches(self, _import_string):
        """Firing an event without subscribers must stay cheap: the handler is not loaded"""
        self.sut.add_action("replace.completed", MagicMock())

        self.sut.do_action("completed", execution())

        _import_string.assert_not_called()

    def test_do_action_should_follow_priority_then_registration_order(self):
        """Lower priority runs first, same priority keeps the registration order"""
        actual = []
        self.sut.add_action("upload.completed", lambda *args, **kwargs: actual.append("first"))
        self.sut.add_action("*.*", lambda *args, **kwargs: actual.append("second"))
        self.sut.add_action("*.completed", lambda *args, **kwargs: actual.append("high_priority"), priority=5)
        self.sut.add_action("upload.*", lambda *args, **kwargs: actual.append("low_priority"), priority=20)

        self.sut.do_action("completed", execution())

        expected = ["high_priority", "first", "second", "low_priority"]
        self.assertListEqual(expected, actual)

    def test_do_action_should_not_stop_if_a_callback_fails(self):
        """A failing subscriber must not prevent the other subscribers from running"""
        _failing = MagicMock(side_effect=Exception("boom"))
        _callback = MagicMock()
        self.sut.add_action("upload.completed", _failing, priority=1)
        self.sut.add_action("upload.completed", _callback)

        with self.assertLogs("importer", level="ERROR"):
            self.sut.do_action("completed", execution())

        _failing.assert_called_once()
        _callback.assert_called_once()

    def test_remove_action_should_remove_only_the_given_callback(self):
        """Removing a callback must keep the other callbacks of the same event"""
        _removed, _kept = MagicMock(), MagicMock()
        self.sut.add_action("upload.completed", _removed)
        self.sut.add_action("upload.completed", _kept)

        self.sut.remove_action("upload.completed", _removed)
        self.sut.do_action("completed", execution())

        _removed.assert_not_called()
        _kept.assert_called_once()

    def test_reset_should_remove_all_callbacks(self):
        """After a reset no callback must run"""
        _callback = MagicMock()
        self.sut.add_action("*.*", _callback)

        self.sut.reset()
        self.sut.do_action("completed", execution())

        _callback.assert_not_called()


class TestBaseImporterSubscriber(GeoNodeBaseTestSupport):
    def test_register_should_be_implemented_by_subclasses(self):
        """A subscriber without register must not be instantiable"""

        class IncompleteSubscriber(BaseImporterSubscriber):
            pass

        with self.assertRaises(TypeError):
            IncompleteSubscriber()


class TestRegisterSubscribers(GeoNodeBaseTestSupport):
    def setUp(self):
        self.sut = ImporterHooks()
        subscriber_callback.reset_mock()

    @override_settings(IMPORTER_HOOK_SUBSCRIBERS=[SUBSCRIBER_PATH])
    def test_register_subscribers_should_register_the_configured_subscribers(self):
        """A subscriber listed in IMPORTER_HOOK_SUBSCRIBERS must receive its events"""
        self.sut.register_subscribers()

        self.sut.do_action("completed", execution())

        subscriber_callback.assert_called_once()

    @override_settings(IMPORTER_HOOK_SUBSCRIBERS=[HANDLER_PATH])
    def test_register_subscribers_should_raise_if_not_a_subscriber(self):
        """A configured class that is not a BaseImporterSubscriber must fail at startup"""
        with self.assertRaises(TypeError):
            self.sut.register_subscribers()

    @override_settings(IMPORTER_HOOK_SUBSCRIBERS=[SUBSCRIBER_PATH])
    def test_register_subscribers_should_keep_actions_added_directly(self):
        """External apps can call add_action in their own ready(): register_subscribers must not drop them"""
        _callback = MagicMock()
        self.sut.add_action("upload.completed", _callback)

        self.sut.register_subscribers()
        self.sut.do_action("completed", execution())

        _callback.assert_called_once()
        subscriber_callback.assert_called_once()
