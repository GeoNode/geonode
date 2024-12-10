#########################################################################
#
# Copyright (C) 2024 OSGeo
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
import json
import os
import shutil
from django.test import TestCase
from geonode.upload.handlers.tiles3d.exceptions import Invalid3DTilesException
from geonode.upload.handlers.tiles3d.handler import Tiles3DFileHandler
from django.contrib.auth import get_user_model
from geonode.upload import project_dir
from geonode.upload.orchestrator import orchestrator
from geonode.upload.models import UploadParallelismLimit
from geonode.upload.api.exceptions import UploadParallelismLimitException
from geonode.base.populate_test_data import create_single_dataset
from osgeo import ogr
from geonode.assets.handlers import asset_handler_registry


class TestTiles3DFileHandler(TestCase):
    databases = ("default", "datastore")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = Tiles3DFileHandler()
        cls.valid_3dtile = f"{project_dir}/tests/fixture/3dtilesample/valid_3dtiles.zip"
        cls.valid_tileset = f"{project_dir}/tests/fixture/3dtilesample/tileset.json"
        cls.valid_tileset_with_region = f"{project_dir}/tests/fixture/3dtilesample/tileset_with_region.json"
        cls.invalid_tileset = f"{project_dir}/tests/fixture/3dtilesample/invalid_tileset.json"
        cls.invalid_3dtile = f"{project_dir}/tests/fixture/3dtilesample/invalid.zip"
        cls.user, _ = get_user_model().objects.get_or_create(username="admin")
        cls.invalid_files = {"base_file": cls.invalid_3dtile}
        cls.valid_files = {"base_file": cls.valid_3dtile}
        cls.owner = get_user_model().objects.exclude(username="AnonymousUser").first()
        cls.layer = create_single_dataset(name="urban_forestry_street_tree_benefits_epsg_26985", owner=cls.owner)
        cls.asset_handler = asset_handler_registry.get_default_handler()
        cls.default_bbox = [-180.0, 180.0, -90.0, 90.0, "EPSG:4326"]

    def test_task_list_is_the_expected_one(self):
        expected = (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.create_geonode_resource",
        )
        self.assertEqual(len(self.handler.TASKS["upload"]), 3)
        self.assertTupleEqual(expected, self.handler.TASKS["upload"])

    def test_task_list_is_the_expected_one_copy(self):
        expected = (
            "start_copy",
            "geonode.upload.copy_geonode_resource",
        )
        self.assertEqual(len(self.handler.TASKS["copy"]), 2)
        self.assertTupleEqual(expected, self.handler.TASKS["copy"])

    def test_is_valid_should_raise_exception_if_the_parallelism_is_met(self):
        parallelism, created = UploadParallelismLimit.objects.get_or_create(slug="default_max_parallel_uploads")
        old_value = parallelism.max_number
        try:
            UploadParallelismLimit.objects.filter(slug="default_max_parallel_uploads").update(max_number=0)

            with self.assertRaises(UploadParallelismLimitException):
                self.handler.is_valid(files=self.valid_files, user=self.user)

        finally:
            parallelism.max_number = old_value
            parallelism.save()

    def test_is_valid_should_pass_with_valid_3dtiles(self):
        self.handler.is_valid(files={"base_file": self.valid_tileset}, user=self.user)

    def test_is_valid_should_raise_exception_if_no_basefile_is_supplied(self):
        data = {"base_file": ""}
        with self.assertRaises(Invalid3DTilesException) as _exc:
            self.handler.is_valid(files=data, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue("base file is not provided" in str(_exc.exception.detail))

    def test_extract_params_from_data(self):
        actual, _data = self.handler.extract_params_from_data(
            _data={"defaults": '{"title":"title_of_the_cloned_resource"}'},
            action="copy",
        )

        self.assertEqual(actual, {"store_spatial_file": True, "title": "title_of_the_cloned_resource"})

    def test_is_valid_should_raise_exception_if_the_3dtiles_is_invalid(self):
        data = {"base_file": "/using/double/dot/in/the/name/is/an/error/file.invalid.json"}
        with self.assertRaises(Invalid3DTilesException) as _exc:
            self.handler.is_valid(files=data, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue("Please remove the additional dots in the filename" in str(_exc.exception.detail))

    def test_is_valid_should_raise_exception_if_the_3dtiles_is_invalid_format(self):
        with self.assertRaises(Invalid3DTilesException) as _exc:
            self.handler.is_valid(files={"base_file": self.invalid_tileset}, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue(
            "The provided 3DTiles is not valid, some of the mandatory keys are missing. Mandatory keys are: 'asset', 'geometricError', 'root'"
            in str(_exc.exception.detail)
        )

    def test_validate_should_raise_exception_for_invalid_asset_key(self):
        _json = {
            "asset": {"invalid_key": ""},
            "geometricError": 1.0,
            "root": {"boundingVolume": {"box": []}, "geometricError": 0.0},
        }
        _path = "/tmp/tileset.json"
        with open(_path, "w") as _f:
            _f.write(json.dumps(_json))
        with self.assertRaises(Invalid3DTilesException) as _exc:
            self.handler.is_valid(files={"base_file": _path}, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue("The mandatory 'version' for the key 'asset' is missing" in str(_exc.exception.detail))
        os.remove(_path)

    def test_validate_should_raise_exception_for_invalid_root_boundingVolume(self):
        _json = {
            "asset": {"version": "1.1"},
            "geometricError": 1.0,
            "root": {"foo": {"box": []}, "geometricError": 0.0},
        }
        _path = "/tmp/tileset.json"
        with open(_path, "w") as _f:
            _f.write(json.dumps(_json))
        with self.assertRaises(Invalid3DTilesException) as _exc:
            self.handler.is_valid(files={"base_file": _path}, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue("The mandatory 'boundingVolume' for the key 'root' is missing" in str(_exc.exception.detail))
        os.remove(_path)

    def test_validate_should_raise_exception_for_invalid_root_geometricError(self):
        _json = {
            "asset": {"version": "1.1"},
            "root": {"boundingVolume": {"box": []}, "foo": 0.0},
        }
        _path = "/tmp/tileset.json"
        with open(_path, "w") as _f:
            _f.write(json.dumps(_json))
        with self.assertRaises(Invalid3DTilesException) as _exc:
            self.handler.is_valid(files={"base_file": _path}, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue(
            "The provided 3DTiles is not valid, some of the mandatory keys are missing. Mandatory keys are: 'asset', 'geometricError', 'root'"
            in str(_exc.exception.detail)
        )
        os.remove(_path)

    def test_get_ogr2ogr_driver_should_return_the_expected_driver(self):
        expected = ogr.GetDriverByName("3dtiles")
        actual = self.handler.get_ogr2ogr_driver()
        self.assertEqual(type(expected), type(actual))

    def test_can_handle_should_return_true_for_3dtiles(self):
        actual = self.handler.can_handle({"base_file": self.valid_tileset})
        self.assertTrue(actual)

    def test_can_handle_should_return_false_for_other_files(self):
        actual = self.handler.can_handle({"base_file": "random.gpkg"})
        self.assertFalse(actual)

    def test_can_handle_should_return_false_if_no_basefile(self):
        actual = self.handler.can_handle({"base_file": ""})
        self.assertFalse(actual)

    def test_supported_file_extension_config(self):
        """
        should return the expected value
        """
        expected = {
            "id": "3dtiles",
            "formats": [
                {
                    "label": "3D Tiles",
                    "required_ext": ["zip"],
                }
            ],
            "actions": list(Tiles3DFileHandler.TASKS.keys()),
            "type": "vector",
        }
        actual = self.handler.supported_file_extension_config
        self.assertDictEqual(actual, expected)

    def test_generate_resource_payload(self):
        exec_id = orchestrator.create_execution_request(
            user=self.owner,
            func_name="funct1",
            step="step",
            input_params={"files": self.valid_files, "skip_existing_layer": True},
        )
        _exec_obj = orchestrator.get_execution_object(exec_id)
        expected = dict(
            resource_type="dataset",
            subtype="3dtiles",
            dirty_state=True,
            title="Layer name",
            owner=self.owner,
            asset="asset",
            link_type="uploaded",
            extension="3dtiles",
            alternate="alternate",
        )

        actual = self.handler.generate_resource_payload("Layer name", "alternate", "asset", _exec_obj, None)
        self.assertSetEqual(set(list(actual.keys())), set(list(expected.keys())))
        self.assertDictEqual(actual, expected)

    def test_create_geonode_resource_validate_bbox_with_region(self):
        shutil.copy(self.valid_tileset_with_region, "/tmp/tileset.json")

        exec_id, asset = self._generate_execid_asset()

        resource = self.handler.create_geonode_resource(
            "layername",
            "layeralternate",
            execution_id=exec_id,
            resource_type="ResourceBase",
            asset=asset,
        )

        # validate bbox
        self.assertFalse(resource.bbox == self.default_bbox)
        expected = [
            -75.6144410959485,
            -75.60974751970046,
            40.040721313841274,
            40.04433990901052,
            "EPSG:4326",
        ]
        self.assertTrue(resource.bbox == expected)

    def test_set_bbox_from_bounding_volume_wit_transform(self):
        # https://github.com/geosolutions-it/MapStore2/blob/master/web/client/api/__tests__/ThreeDTiles-test.js#L102-L146
        tilesetjson_file = {
            "asset": {"version": "1.1"},
            "geometricError": 1.0,
            "root": {
                "transform": [
                    96.86356343768793,
                    24.848542777253734,
                    0,
                    0,
                    -15.986465724980844,
                    62.317780594908875,
                    76.5566922962899,
                    0,
                    19.02322243409411,
                    -74.15554020821229,
                    64.3356267137516,
                    0,
                    1215107.7612304366,
                    -4736682.902037748,
                    4081926.095098698,
                    1,
                ],
                "boundingVolume": {
                    "box": [0, 0, 0, 7.0955, 0, 0, 0, 3.1405, 0, 0, 0, 5.0375],
                },
            },
        }

        with open("/tmp/tileset.json", "w+") as js_file:
            js_file.write(json.dumps(tilesetjson_file))

        exec_id, asset = self._generate_execid_asset()

        resource = self.handler.create_geonode_resource(
            "layername",
            "layeralternate",
            execution_id=exec_id,
            resource_type="ResourceBase",
            asset=asset,
        )
        self.assertFalse(resource.bbox == self.default_bbox)

        self.assertEqual(resource.bbox_x0, -75.61852101302848)
        self.assertEqual(resource.bbox_x1, -75.60566760262047)
        self.assertEqual(resource.bbox_y0, 40.03610390613993)
        self.assertEqual(resource.bbox_y1, 40.04895731654794)

        os.remove("/tmp/tileset.json")

    def test_set_bbox_from_bounding_volume_without_transform(self):
        # https://github.com/geosolutions-it/MapStore2/blob/master/web/client/api/__tests__/ThreeDTiles-test.js#L147-L180
        tilesetjson_file = {
            "asset": {"version": "1.1"},
            "geometricError": 1.0,
            "root": {
                "boundingVolume": {
                    "box": [
                        0.2524109,
                        9.536743e-7,
                        4.5,
                        16.257824,
                        0.0,
                        0.0,
                        0.0,
                        -19.717258,
                        0.0,
                        0.0,
                        0.0,
                        4.5,
                    ]
                }
            },
        }

        with open("/tmp/tileset.json", "w+") as js_file:
            js_file.write(json.dumps(tilesetjson_file))

        exec_id, asset = self._generate_execid_asset()

        resource = self.handler.create_geonode_resource(
            "layername",
            "layeralternate",
            execution_id=exec_id,
            resource_type="ResourceBase",
            asset=asset,
        )
        self.assertFalse(resource.bbox == self.default_bbox)

        self.assertEqual(resource.bbox_x0, -1.3348442882497923e-05)
        self.assertEqual(resource.bbox_x1, 0.0004463052796897286)
        self.assertEqual(resource.bbox_y0, 86.81078622278615)
        self.assertEqual(resource.bbox_y1, 86.81124587650872)

        os.remove("/tmp/tileset.json")

    def test_set_bbox_from_bounding_volume_sphere_with_transform(self):
        # https://github.com/geosolutions-it/MapStore2/blob/master/web/client/api/__tests__/ThreeDTiles-test.js#L102-L146
        tilesetjson_file = {
            "asset": {"version": "1.1"},
            "geometricError": 1.0,
            "root": {
                "transform": [
                    0.968635634376879,
                    0.24848542777253735,
                    0,
                    0,
                    -0.15986460794399626,
                    0.6231776137472074,
                    0.7655670897127491,
                    0,
                    0.190232265775849,
                    -0.7415555636019701,
                    0.6433560687121489,
                    0,
                    1215012.8828876738,
                    -4736313.051199594,
                    4081605.22126042,
                    1,
                ],
                "boundingVolume": {"sphere": [0, 0, 0, 5]},
            },
        }

        with open("/tmp/tileset.json", "w+") as js_file:
            js_file.write(json.dumps(tilesetjson_file))

        exec_id, asset = self._generate_execid_asset()

        resource = self.handler.create_geonode_resource(
            "layername",
            "layeralternate",
            execution_id=exec_id,
            resource_type="ResourceBase",
            asset=asset,
        )
        self.assertFalse(resource.bbox == self.default_bbox)

        self.assertAlmostEqual(resource.bbox_x0, -75.61213927392595)
        self.assertAlmostEqual(resource.bbox_x1, -75.61204934172301)
        self.assertAlmostEqual(resource.bbox_y0, 40.042485645323616)
        self.assertAlmostEqual(resource.bbox_y1, 40.042575577526556)

        os.remove("/tmp/tileset.json")

    def test_set_bbox_from_bounding_volume_sphere_without_transform(self):
        # https://github.com/geosolutions-it/MapStore2/blob/master/web/client/api/__tests__/ThreeDTiles-test.js#L53C4-L79C8
        tilesetjson_file = {
            "asset": {"version": "1.1"},
            "geometricError": 1.0,
            "root": {"boundingVolume": {"sphere": [0.2524109, 9.536743e-7, 4.5, 5]}},
        }

        with open("/tmp/tileset.json", "w+") as js_file:
            js_file.write(json.dumps(tilesetjson_file))

        exec_id, asset = self._generate_execid_asset()

        resource = self.handler.create_geonode_resource(
            "layername",
            "layeralternate",
            execution_id=exec_id,
            resource_type="ResourceBase",
            asset=asset,
        )
        self.assertFalse(resource.bbox == self.default_bbox)

        self.assertEqual(resource.bbox_x0, 0.00017151231693387494)
        self.assertEqual(resource.bbox_x1, 0.00026144451987335574)
        self.assertEqual(resource.bbox_y0, 86.81097108354597)
        self.assertEqual(resource.bbox_y1, 86.8110610157489)

        os.remove("/tmp/tileset.json")

    def test_set_bbox_from_bounding_volume_sphere_with_center_zero_without_transform(self):
        # https://github.com/geosolutions-it/MapStore2/blob/master/web/client/api/__tests__/ThreeDTiles-test.js#L53C4-L79C8
        # This test should not extract bbox from boundingVolume sphere with center 0, 0, 0
        tilesetjson_file = {
            "asset": {"version": "1.1"},
            "geometricError": 1.0,
            "root": {"boundingVolume": {"sphere": [0, 0, 0, 5]}},
        }

        with open("/tmp/tileset.json", "w+") as js_file:
            js_file.write(json.dumps(tilesetjson_file))

        exec_id, asset = self._generate_execid_asset()

        resource = self.handler.create_geonode_resource(
            "layername",
            "layeralternate",
            execution_id=exec_id,
            resource_type="ResourceBase",
            asset=asset,
        )
        self.assertTrue(resource.bbox == self.default_bbox)

        os.remove("/tmp/tileset.json")

    def _generate_execid_asset(self):
        exec_id = orchestrator.create_execution_request(
            user=self.owner,
            func_name="funct1",
            step="step",
            input_params={
                "files": {"base_file": "/tmp/tileset.json"},
                "skip_existing_layer": True,
            },
        )
        asset = self.asset_handler.create(
            title="Original",
            owner=self.owner,
            description=None,
            type=str(self.handler),
            files=["/tmp/tileset.json"],
            clone_files=False,
        )

        return exec_id, asset
