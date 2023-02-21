from unittest.mock import create_autospec, patch

from geonode.base.populate_test_data import all_public, create_models, remove_models
from geonode.geoserver.tasks import geoserver_create_style, geoserver_set_style
from geonode.geoserver.signals import geoserver_automatic_default_style_set
from geonode.layers.models import Dataset
from geonode.layers.populate_datasets_data import create_dataset_data
from geonode.tests.base import GeoNodeBaseTestSupport


class TasksTest(GeoNodeBaseTestSupport):
    type = "dataset"

    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_models(type=cls.get_type, integration=cls.get_integration)
        all_public()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    def setUp(self):
        super().setUp()
        create_dataset_data()

    def mock_signal_callback(self, instance, **kwargs):
        pass

    def test_geoserver_style_visual_mode_automatically_with_sld_file(self):
        dataset = Dataset.objects.first()
        sld_file = "geonode/base/fixtures/test_sld.sld"
        handler = create_autospec(self.mock_signal_callback)

        geoserver_automatic_default_style_set.connect(handler)
        with patch("geoserver.catalog.Catalog.get_style") as style_mck:
            style_mck.return_value = True
            geoserver_create_style(dataset.id, dataset.name, sld_file=sld_file, tempdir=None)
            self.assertEqual(handler.call_count, 0)

    def test_geoserver_style_visual_mode_automatically_without_sld_file(self):
        dataset = Dataset.objects.first()
        handler = create_autospec(self.mock_signal_callback)

        geoserver_automatic_default_style_set.connect(handler)
        geoserver_create_style(dataset.id, dataset.name, sld_file=None, tempdir=None)
        handler.assert_called_once_with(signal=geoserver_automatic_default_style_set, sender=dataset, instance=dataset)

    @patch("geonode.geoserver.tasks.set_dataset_style")
    def test_geoserver_set_style_with_real_file(self, mocked_set_dataset_style):
        dataset = Dataset.objects.first()
        sld_file = "geonode/base/fixtures/test_sld.sld"
        geoserver_set_style(instance_id=dataset.id, base_file=sld_file)
        mocked_set_dataset_style.assert_called_once()

        args_list = mocked_set_dataset_style.call_args_list[0].args
        kwargs_list = mocked_set_dataset_style.call_args_list[0].kwargs
        self.assertEqual(args_list[0].id, dataset.id)
        self.assertEqual(args_list[1], dataset.alternate)
        self.assertIsInstance(args_list[2], bytes)

        self.assertDictEqual({"base_file": sld_file}, kwargs_list)

    @patch("geonode.geoserver.tasks.set_dataset_style")
    def test_geoserver_set_style_with_xml(self, mocked_set_dataset_style):
        dataset = Dataset.objects.first()

        with open("geonode/base/fixtures/test_sld.sld", "r+") as _file:
            geoserver_set_style(instance_id=dataset.id, base_file=_file.read())
        mocked_set_dataset_style.assert_called_once()

        args_list = mocked_set_dataset_style.call_args_list[0].args
        kwargs_list = mocked_set_dataset_style.call_args_list[0].kwargs
        self.assertEqual(args_list[0].id, dataset.id)
        self.assertEqual(args_list[1], dataset.alternate)
        self.assertIsInstance(args_list[2], str)

        self.assertDictEqual({"base_file": None}, kwargs_list)
