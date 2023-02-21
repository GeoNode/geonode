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

from django.test import override_settings

from geonode.harvesting import config
from geonode.tests.base import GeoNodeBaseSimpleTestSupport


class ConfigTestCase(GeoNodeBaseSimpleTestSupport):
    @override_settings(HARVESTER_CLASSES=[])
    def test_default_config_harvester_classes(self):
        self.assertEqual(config.get_setting("HARVESTER_CLASSES"), config._DEFAULT_HARVESTERS)

    def test_custom_harvester_classes(self):
        phony_class_paths = [
            "fake_harvester1",
            "fake_harvester2",
        ]
        with self.settings(HARVESTER_CLASSES=phony_class_paths):
            self.assertEqual(config.get_setting("HARVESTER_CLASSES"), config._DEFAULT_HARVESTERS + phony_class_paths)

    def test_harvester_classes_dont_repeat(self):
        phony_class_paths = [
            "fake_harvester1",
            "fake_harvester2",
        ]
        repeated_paths = [
            "fake_harvester1",
        ]
        with self.settings(HARVESTER_CLASSES=phony_class_paths + repeated_paths):
            self.assertEqual(config.get_setting("HARVESTER_CLASSES"), config._DEFAULT_HARVESTERS + phony_class_paths)
