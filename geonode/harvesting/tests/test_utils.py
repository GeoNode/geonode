from unittest import mock

from django.test import SimpleTestCase

from .. import utils


class UtilsTestCase(SimpleTestCase):

    @mock.patch("geonode.harvesting.utils.jsonschema")
    @mock.patch("geonode.harvesting.utils.import_string")
    def test_validate_worker_configuration(self, mock_import_string, mock_jsonschema):
        extra_config_schema = "fake_config_schema"
        mock_worker_class = mock.MagicMock()
        mock_worker_class.get_extra_config_schema.return_value = extra_config_schema
        mock_import_string.return_value = mock_worker_class

        harvester_type = "fake_harvester_type"
        configuration = "fake_configuration"
        utils.validate_worker_configuration(harvester_type, configuration)

        mock_import_string.assert_called_with(harvester_type)
        mock_worker_class.get_extra_config_schema.assert_called()
        mock_jsonschema.validate.assert_called_with(configuration, extra_config_schema)