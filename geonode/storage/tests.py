# -*- coding: utf-8 -*-
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
# along with this profgram. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import io

from unittest.mock import patch

from django.test.testcases import SimpleTestCase

from geonode.storage.aws import AwsStorageManager
from geonode.storage.gcs import GoogleStorageManager
from geonode.storage.dropbox import DropboxStorageManager


class TestDropboxStorageManager(SimpleTestCase):
    def setUp(self):
        self.sut = DropboxStorageManager

    @patch('geonode.storage.dropbox.DropBoxStorage.delete')
    def test_dropbox_deleted_has_been_called(self, dbx):
        '''
        Will test that the function returns the expected result
        and that the DropBoxStorage function as been called with the expected parameters
        '''
        dbx.return_value = None
        output = self.sut().delete('filename')
        self.assertIsNone(output)
        dbx.assert_called_once_with('filename')

    @patch('geonode.storage.dropbox.DropBoxStorage.exists')
    def test_dropbox_exists_has_been_called(self, dbx):
        '''
        Will test that the function returns the expected result
        and that the DropBoxStorage function as been called with the expected parameters
        '''
        dbx.return_value = True
        output = self.sut().exists('filename')
        self.assertTrue(output)
        dbx.assert_called_once_with('filename')

    @patch('geonode.storage.dropbox.DropBoxStorage.listdir')
    def test_dropbox_listdir_has_been_called(self, dbx):
        '''
        Will test that the function returns the expected result
        and that the DropBoxStorage function as been called with the expected parameters
        '''
        dbx.return_value = (['folder1'], ['file1', 'file2'])
        output = self.sut().listdir('Apps/')
        self.assertTupleEqual((['folder1'], ['file1', 'file2']), output)
        dbx.assert_called_once_with('Apps/')

    @patch('geonode.storage.dropbox.DropBoxStorage._open')
    def test_dropbox_open_has_been_called(self, dbx):
        '''
        Will test that the function returns the expected result
        and that the DropBoxStorage function as been called with the expected parameters
        '''
        dbx.return_value = io.StringIO()
        output = self.sut().open("name", mode='xx')
        self.assertEqual(type(output), io.StringIO().__class__)
        dbx.assert_called_once_with("name", mode='xx')

    @patch('geonode.storage.dropbox.DropBoxStorage._full_path')
    def test_dropbox_path_has_been_called(self, dbx):
        '''
        Will test that the function returns the expected result
        and that the DropBoxStorage function as been called with the expected parameters
        '''
        dbx.return_value = "/opt/full/path/to/file"
        output = self.sut().path('file')
        self.assertEqual("/opt/full/path/to/file", output)
        dbx.assert_called_once_with('file')

    @patch('geonode.storage.dropbox.DropBoxStorage._save')
    def test_dropbox_save_has_been_called(self, dbx):
        '''
        Will test that the function returns the expected result
        and that the DropBoxStorage function as been called with the expected parameters
        '''
        dbx.return_value = "cleaned_name"
        output = self.sut().save('file_name', "content")
        self.assertEqual("cleaned_name", output)
        dbx.assert_called_once_with('file_name', "content")

    @patch('geonode.storage.dropbox.DropBoxStorage.size')
    def test_dropbox_size_has_been_called(self, dbx):
        '''
        Will test that the function returns the expected result
        and that the DropBoxStorage function as been called with the expected parameters
        '''
        dbx.return_value = 1
        output = self.sut().size('name')
        self.assertEqual(1, output)
        dbx.assert_called_once_with('name')


class TestGoogleStorageManager(SimpleTestCase):
    def setUp(self):
        self.sut = GoogleStorageManager

    @patch('storages.backends.gcloud.GoogleCloudStorage.delete')
    def test_google_deleted_has_been_called(self, gcs):
        '''
        Will test that the function returns the expected result
        and that the GoogleCloudStorage function as been called with the expected parameters
        '''
        gcs.return_value = None
        output = self.sut().delete('filename')
        self.assertIsNone(output)
        gcs.assert_called_once_with('filename')

    @patch('storages.backends.gcloud.GoogleCloudStorage.exists')
    def test_google_exists_has_been_called(self, gcs):
        '''
        Will test that the function returns the expected result
        and that the GoogleCloudStorage function as been called with the expected parameters
        '''
        gcs.return_value = True
        output = self.sut().exists('filename')
        self.assertTrue(output)
        gcs.assert_called_once_with('filename')

    @patch('storages.backends.gcloud.GoogleCloudStorage.listdir')
    def test_google_listdir_has_been_called(self, gcs):
        '''
        Will test that the function returns the expected result
        and that the GoogleCloudStorage function as been called with the expected parameters
        '''
        gcs.return_value = (['folder1'], ['file1', 'file2'])
        output = self.sut().listdir('Apps/')
        self.assertTupleEqual((['folder1'], ['file1', 'file2']), output)
        gcs.assert_called_once_with('Apps/')

    @patch('storages.backends.gcloud.GoogleCloudStorage._open')
    def test_google_open_has_been_called(self, gcs):
        '''
        Will test that the function returns the expected result
        and that the GoogleCloudStorage function as been called with the expected parameters
        '''
        gcs.return_value = io.StringIO()
        output = self.sut().open("name", mode='xx')
        self.assertEqual(type(output), io.StringIO().__class__)
        gcs.assert_called_once_with("name", mode='xx')

    def test_google_path_has_been_called(self):
        '''
        Will test that the function returns the expected result
        and that the GoogleCloudStorage function as been called with the expected parameters
        '''
        with self.assertRaises(NotImplementedError):
            self.sut().path('file')

    @patch('storages.backends.gcloud.GoogleCloudStorage._save')
    def test_google_save_has_been_called(self, gcs):
        '''
        Will test that the function returns the expected result
        and that the GoogleCloudStorage function as been called with the expected parameters
        '''
        gcs.return_value = "cleaned_name"
        output = self.sut().save('file_name', "content")
        self.assertEqual("cleaned_name", output)
        gcs.assert_called_once_with('file_name', "content")

    @patch('storages.backends.gcloud.GoogleCloudStorage.size')
    def test_google_size_has_been_called(self, gcs):
        '''
        Will test that the function returns the expected result
        and that the GoogleCloudStorage function as been called with the expected parameters
        '''
        gcs.return_value = 1
        output = self.sut().size('name')
        self.assertEqual(1, output)
        gcs.assert_called_once_with('name')


class TestAwsStorageManager(SimpleTestCase):
    def setUp(self):
        self.sut = AwsStorageManager

    @patch('storages.backends.s3boto3.S3Boto3Storage.delete')
    def test_aws_deleted_has_been_called(self, aws):
        '''
        Will test that the function returns the expected result
        and that the AwsStorageManager function as been called with the expected parameters
        '''
        aws.return_value = None
        output = self.sut().delete('filename')
        self.assertIsNone(output)
        aws.assert_called_once_with('filename')

    @patch('storages.backends.s3boto3.S3Boto3Storage.exists')
    def test_aws_exists_has_been_called(self, aws):
        '''
        Will test that the function returns the expected result
        and that the AwsStorageManager function as been called with the expected parameters
        '''
        aws.return_value = True
        output = self.sut().exists('filename')
        self.assertTrue(output)
        aws.assert_called_once_with('filename')

    @patch('storages.backends.s3boto3.S3Boto3Storage.listdir')
    def test_aws_listdir_has_been_called(self, aws):
        '''
        Will test that the function returns the expected result
        and that the AwsStorageManager function as been called with the expected parameters
        '''
        aws.return_value = (['folder1'], ['file1', 'file2'])
        output = self.sut().listdir('Apps/')
        self.assertTupleEqual((['folder1'], ['file1', 'file2']), output)
        aws.assert_called_once_with('Apps/')

    @patch('storages.backends.s3boto3.S3Boto3Storage._open')
    def test_aws_open_has_been_called(self, aws):
        '''
        Will test that the function returns the expected result
        and that the AwsStorageManager function as been called with the expected parameters
        '''
        aws.return_value = io.StringIO()
        output = self.sut().open("name", mode='xx')
        self.assertEqual(type(output), io.StringIO().__class__)
        aws.assert_called_once_with("name", mode='xx')

    @patch('storages.backends.s3boto3.S3Boto3Storage._normalize_name')
    def test_aws_path_has_been_called(self, aws):
        '''
        Will test that the function returns the expected result
        and that the AwsStorageManager function as been called with the expected parameters
        '''
        aws.return_value = "/opt/full/path/to/file"
        output = self.sut().path('file')
        self.assertEqual("/opt/full/path/to/file", output)
        aws.assert_called_once_with('file')

    @patch('storages.backends.s3boto3.S3Boto3Storage._save')
    def test_aws_save_has_been_called(self, aws):
        '''
        Will test that the function returns the expected result
        and that the AwsStorageManager function as been called with the expected parameters
        '''
        aws.return_value = True
        output = self.sut().save('file_name', "content")
        self.assertTrue(output)
        aws.assert_called_once_with('file_name', "content")

    @patch('storages.backends.s3boto3.S3Boto3Storage.size')
    def test_aws_size_has_been_called(self, aws):
        '''
        Will test that the function returns the expected result
        and that the AwsStorageManager function as been called with the expected parameters
        '''
        aws.return_value = 1
        output = self.sut().size('name')
        self.assertEqual(1, output)
        aws.assert_called_once_with('name')
