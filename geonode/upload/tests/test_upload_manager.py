import os
from django.test import TestCase
from gisdata import GOOD_DATA
from geonode.upload.models import Upload, UploadFile
from geonode.base.populate_test_data import create_single_layer
from unittest.mock import patch


class TestUploadFileManager(TestCase):
    def setUp(self):
        self.sut = UploadFile
        self.file = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        self.layer = create_single_layer('foo_layer')
        self.upload = Upload.objects.create(
            state='RUNNING',
            layer=self.layer
        )

    def test_will_return_none_if_file_does_not_exists(self):
        actual = self.sut.objects.create_from_upload(
                self.upload,
                "foo_name",
                "not_exising_file"
            )
        self.assertIsNone(actual)
        # check also that UploadFile does not exist
        uf = UploadFile.objects.filter(upload=self.upload).exists()
        self.assertFalse(uf)

    @patch('geonode.storage.manager.storage_manager.save')
    def test_will_create_the_upload_file_row(self, save):
        save.return_value = self.file
        actual = self.sut.objects.create_from_upload(
                self.upload,
                "foo_name",
                self.file
            )
        self.assertIsNotNone(actual)
        # check also that UploadFile does not exist
        uf = UploadFile.objects.filter(upload=self.upload).exists()
        self.assertTrue(uf)