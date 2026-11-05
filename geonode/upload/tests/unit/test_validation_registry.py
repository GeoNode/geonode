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

"""unit tests for geonode.upload.validation"""

from types import MappingProxyType

from django.test import SimpleTestCase, override_settings

from geonode.upload.handlers.base import BaseHandler
from geonode.upload.validation import FileValidationConfigRegistry
from geonode.upload.validation.base import ValidationConfigProvider

EMPTY_CONFIG = {
    "allowed_extensions": frozenset(),
    "magic_mimetype_map": {},
    "magic_description_map": {},
}


class _FakeHandler(BaseHandler):
    upload_validation_config = {
        "shp": {"description_contains": {"ESRI Shapefile"}},
        "xml": {"mimes": {"application/xml"}},
    }


class _OverlappingHandler(BaseHandler):
    upload_validation_config = {
        "xml": {"mimes": {"text/xml"}, "description_contains": {"XML"}},
    }


class _EmptyHandler(BaseHandler):
    """Handler that does not declare upload_validation_config."""


class BaseHandlerValidationConfigTests(SimpleTestCase):
    """Cover the merge / read classmethods on BaseHandler."""

    def setUp(self):
        self._saved = BaseHandler.UPLOAD_VALIDATION_CONFIG
        BaseHandler.UPLOAD_VALIDATION_CONFIG = EMPTY_CONFIG

    def tearDown(self):
        BaseHandler.UPLOAD_VALIDATION_CONFIG = self._saved

    def test_merge_unions_mimes_and_descriptions_across_handlers(self):
        _FakeHandler.merge_upload_validation_config()
        _OverlappingHandler.merge_upload_validation_config()
        merged = BaseHandler.UPLOAD_VALIDATION_CONFIG

        self.assertEqual(merged["allowed_extensions"], frozenset({"shp", "xml"}))
        self.assertEqual(merged["magic_mimetype_map"]["xml"], frozenset({"application/xml", "text/xml"}))
        self.assertEqual(merged["magic_description_map"]["shp"], frozenset({"ESRI Shapefile"}))
        self.assertEqual(merged["magic_description_map"]["xml"], frozenset({"XML"}))

    def test_handler_without_property_contributes_nothing(self):
        _EmptyHandler.merge_upload_validation_config()
        self.assertEqual(BaseHandler.UPLOAD_VALIDATION_CONFIG, EMPTY_CONFIG)

    def test_extension_with_only_mimes_omits_description_entry(self):
        _FakeHandler.merge_upload_validation_config()
        merged = BaseHandler.UPLOAD_VALIDATION_CONFIG
        self.assertNotIn("xml", merged["magic_description_map"])
        self.assertIn("xml", merged["magic_mimetype_map"])


class _DummyProvider(ValidationConfigProvider):
    def url_names(self):
        return ("dummy_url",)

    def build_config(self):
        return {"allowed_extensions": frozenset({"foo"}), "magic_mimetype_map": {"foo": frozenset({"text/plain"})}}


class _SecondProvider(ValidationConfigProvider):
    def url_names(self):
        return ("second_url",)

    def build_config(self):
        return {"allowed_extensions": frozenset({"bar"}), "magic_mimetype_map": {"bar": frozenset({"text/plain"})}}


class _OverridingProvider(ValidationConfigProvider):
    """Claims the same URL name as _DummyProvider so we can verify warning behaviour."""

    def url_names(self):
        return ("dummy_url",)

    def build_config(self):
        return {"allowed_extensions": frozenset({"baz"}), "magic_mimetype_map": {"baz": frozenset({"text/plain"})}}


class _EmptyProvider(ValidationConfigProvider):
    def url_names(self):
        return ("noop",)

    def build_config(self):
        return {}


class RegistryTests(SimpleTestCase):
    def setUp(self):
        FileValidationConfigRegistry.clear()

    def tearDown(self):
        FileValidationConfigRegistry.clear()

    def test_install_freezes_payload(self):
        FileValidationConfigRegistry.install({"x": {"allowed_extensions": frozenset()}})
        cfg = FileValidationConfigRegistry.get("x")
        self.assertIsInstance(cfg, MappingProxyType)
        with self.assertRaises(TypeError):
            cfg["allowed_extensions"] = frozenset({"y"})

    def test_get_returns_none_for_unknown(self):
        self.assertIsNone(FileValidationConfigRegistry.get("missing"))
        self.assertIsNone(FileValidationConfigRegistry.get(None))

    def test_rebuild_runs_listed_providers_only(self):
        FileValidationConfigRegistry.rebuild(
            provider_paths=[
                "geonode.upload.tests.unit.test_validation_registry._DummyProvider",
                "geonode.upload.tests.unit.test_validation_registry._SecondProvider",
            ]
        )
        self.assertIn("foo", FileValidationConfigRegistry.get("dummy_url")["allowed_extensions"])
        self.assertIn("bar", FileValidationConfigRegistry.get("second_url")["allowed_extensions"])

    def test_rebuild_skips_empty_provider(self):
        FileValidationConfigRegistry.rebuild(
            provider_paths=[
                "geonode.upload.tests.unit.test_validation_registry._DummyProvider",
                "geonode.upload.tests.unit.test_validation_registry._EmptyProvider",
            ]
        )
        # _EmptyProvider's URL must not be installed.
        self.assertIsNone(FileValidationConfigRegistry.get("noop"))
        self.assertIsNotNone(FileValidationConfigRegistry.get("dummy_url"))

    def test_later_provider_overrides_earlier_for_same_url(self):
        FileValidationConfigRegistry.rebuild(
            provider_paths=[
                "geonode.upload.tests.unit.test_validation_registry._DummyProvider",
                "geonode.upload.tests.unit.test_validation_registry._OverridingProvider",
            ]
        )
        self.assertIn("baz", FileValidationConfigRegistry.get("dummy_url")["allowed_extensions"])
        self.assertNotIn("foo", FileValidationConfigRegistry.get("dummy_url")["allowed_extensions"])

    @override_settings(
        FILE_VALIDATION_CONFIGURATION_PROVIDERS=[
            "geonode.upload.tests.unit.test_validation_registry._DummyProvider",
        ],
    )
    def test_rebuild_default_reads_from_settings(self):
        FileValidationConfigRegistry.rebuild()
        self.assertIsNotNone(FileValidationConfigRegistry.get("dummy_url"))

    def test_clear_empties_registry(self):
        FileValidationConfigRegistry.install({"x": {"allowed_extensions": frozenset()}})
        FileValidationConfigRegistry.clear()
        self.assertIsNone(FileValidationConfigRegistry.get("x"))
