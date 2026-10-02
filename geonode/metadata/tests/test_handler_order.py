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

from django.test import SimpleTestCase

from geonode.metadata.apps import setup_metadata_handlers
from geonode.metadata.manager import (
    MetadataManager,
    metadata_manager,
    HANDLER_ORDER_INITIAL,
    HANDLER_ORDER_DEFAULT,
    HANDLER_ORDER_FINAL,
)
from geonode.metadata.tests.handlers import FakeHandler


class HandlerOrderTests(SimpleTestCase):
    """
    The handlers are called in the order they are stored in: an external module may register its
    own at any moment, so the position can not be left to the registration sequence
    """

    def setUp(self):
        self.manager = MetadataManager()

    def ids(self):
        return list(self.manager.handlers)

    def test_handlers_are_called_in_registration_order_by_default(self):
        for handler_id in ("first", "second", "third"):
            self.manager.add_handler(handler_id, FakeHandler)

        self.assertEqual(["first", "second", "third"], self.ids())

    def test_a_final_handler_stays_last_even_if_registered_first(self):
        self.manager.add_handler("tracker", FakeHandler, order=HANDLER_ORDER_FINAL)
        self.manager.add_handler("rndt", FakeHandler)
        self.manager.add_handler("inspire", FakeHandler)

        self.assertEqual(["rndt", "inspire", "tracker"], self.ids())

    def test_an_initial_handler_stays_first_even_if_registered_last(self):
        self.manager.add_handler("rndt", FakeHandler)
        self.manager.add_handler("cleaner", FakeHandler, order=HANDLER_ORDER_INITIAL)

        self.assertEqual(["cleaner", "rndt"], self.ids())

    def test_the_three_groups_keep_their_relative_position(self):
        # registered in the most unfavourable sequence
        self.manager.add_handler("tracker", FakeHandler, order=HANDLER_ORDER_FINAL)
        self.manager.add_handler("rndt", FakeHandler, order=HANDLER_ORDER_DEFAULT)
        self.manager.add_handler("cleaner", FakeHandler, order=HANDLER_ORDER_INITIAL)

        self.assertEqual(["cleaner", "rndt", "tracker"], self.ids())

    def test_handlers_of_the_same_group_keep_their_registration_sequence(self):
        self.manager.add_handler("base", FakeHandler)
        self.manager.add_handler("tracker", FakeHandler, order=HANDLER_ORDER_FINAL)
        self.manager.add_handler("rndt", FakeHandler)
        self.manager.add_handler("inspire", FakeHandler)

        self.assertEqual(["base", "rndt", "inspire", "tracker"], self.ids())

    def test_two_external_modules_keep_the_order_their_apps_are_listed_in(self):
        # geonode registers its own handlers, then every app adds its own from its ready()
        self.manager.add_handler("metadata_cleaner", FakeHandler, order=HANDLER_ORDER_INITIAL)
        self.manager.add_handler("base", FakeHandler)
        self.manager.add_handler("multilang", FakeHandler, order=HANDLER_ORDER_FINAL)
        self.manager.add_handler("rndt", FakeHandler)  # first app in INSTALLED_APPS
        self.manager.add_handler("inspire", FakeHandler)  # second app

        self.assertEqual(["metadata_cleaner", "base", "rndt", "inspire", "multilang"], self.ids())

    def test_an_external_module_does_not_need_to_know_about_the_order(self):
        # how geonode-rndt and geonode-inspire register, from their own AppConfig.ready()
        self.manager.add_handler("tracker", FakeHandler, order=HANDLER_ORDER_FINAL)
        self.manager.add_handler("rndt", FakeHandler)

        self.assertEqual(HANDLER_ORDER_DEFAULT, self.manager.handler_orders["rndt"])
        self.assertEqual(["rndt", "tracker"], self.ids())

    def test_handlers_put_in_place_without_add_handler_are_not_a_problem(self):
        # some tests build their own manager assigning the whole dict: those handlers carry no order
        self.manager.handlers = {"loader": FakeHandler(), "sparse": FakeHandler()}
        self.manager.add_handler("tracker", FakeHandler, order=HANDLER_ORDER_FINAL)
        self.manager.add_handler("cleaner", FakeHandler, order=HANDLER_ORDER_INITIAL)

        self.assertEqual(["cleaner", "loader", "sparse", "tracker"], self.ids())

    def test_re_registering_a_handler_moves_it_to_the_new_order(self):
        self.manager.add_handler("base", FakeHandler)
        self.manager.add_handler("rndt", FakeHandler)
        self.manager.add_handler("rndt", FakeHandler, order=HANDLER_ORDER_INITIAL)

        self.assertEqual(["rndt", "base"], self.ids())
        self.assertEqual(2, len(self.manager.handlers))


class SetupMetadataHandlersTests(SimpleTestCase):
    """
    Registration of the declared handlers, where the group an entry belongs to sets its order
    """

    FAKE = "geonode.metadata.tests.handlers.FakeHandler"

    def setup_with(self, initial, middle, final):
        manager = MetadataManager()
        with (
            patch("geonode.metadata.manager.metadata_manager", manager),
            patch("geonode.metadata.settings.INITIAL_METADATA_HANDLERS", initial),
            patch("geonode.metadata.settings.METADATA_HANDLERS", middle),
            patch("geonode.metadata.settings.FINAL_METADATA_HANDLERS", final),
        ):
            setup_metadata_handlers()
        return manager

    def test_each_group_gets_its_own_order(self):
        manager = self.setup_with({"cleaner": self.FAKE}, {"base": self.FAKE}, {"tracker": self.FAKE})

        self.assertEqual(["cleaner", "base", "tracker"], list(manager.handlers))
        self.assertEqual(HANDLER_ORDER_INITIAL, manager.handler_orders["cleaner"])
        self.assertEqual(HANDLER_ORDER_DEFAULT, manager.handler_orders["base"])
        self.assertEqual(HANDLER_ORDER_FINAL, manager.handler_orders["tracker"])

    def test_a_handler_declared_in_two_groups_is_warned_about(self):
        # the last group wins silently otherwise, dragging the handler out of its group
        with self.assertLogs("geonode.metadata.apps", level="WARNING") as logged:
            manager = self.setup_with({"cleaner": self.FAKE}, {"cleaner": self.FAKE}, {})

        self.assertTrue([line for line in logged.output if "'cleaner' is declared in more than one group" in line])
        self.assertEqual(HANDLER_ORDER_DEFAULT, manager.handler_orders["cleaner"])

    def test_the_registered_handlers_run_cleaner_first_and_tracker_last(self):
        # the manager is the authoritative list: the settings only cover what geonode itself declares
        registered = list(metadata_manager.handlers)

        self.assertEqual("metadata_cleaner", registered[0])
        self.assertEqual("tracker", registered[-1])
        # multilang localizes what the handlers before it added, the tracker reads what they all left
        self.assertLess(registered.index("multilang"), registered.index("tracker"))
