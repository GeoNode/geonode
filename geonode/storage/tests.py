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
import os
import shutil
import gisdata
from unittest.mock import patch

from django.test.testcases import SimpleTestCase, TestCase

from geonode.utils import mkdtemp
from geonode.storage.aws import AwsStorageManager
from geonode.storage.exceptions import DataRetrieverExcepion
from geonode.storage.manager import StorageManager
from geonode.storage.gcs import GoogleStorageManager
from geonode.storage.dropbox import DropboxStorageManager
from geonode.base.populate_test_data import create_single_dataset


class TestDropboxStorageManager(SimpleTestCase):

    def setUp(self):
        with self.settings(DROPBOX_OAUTH2_TOKEN="auth_token"):
            self.sut = DropboxStorageManager()

    @patch('geonode.storage.dropbox.DropBoxStorage.delete')
    def test_dropbox_deleted(self, dbx):
        '''
        Will test that the function returns the expected result
        and that the DropBoxStorage function as been called with the expected parameters
        '''
        dbx.return_value = None
        output = self.sut.delete('filename')
        self.assertIsNone(output)
        dbx.assert_called_once_with('filename')

    @patch('geonode.storage.dropbox.DropBoxStorage.exists')
    def test_dropbox_exists(self, dbx):
        '''
        Will test that the function returns the expected result
        and that the DropBoxStorage function as been called with the expected parameters
        '''
        dbx.return_value = True
        output = self.sut.exists('filename')
        self.assertTrue(output)
        dbx.assert_called_once_with('filename')

    @patch('geonode.storage.dropbox.DropBoxStorage.listdir')
    def test_dropbox_listdir(self, dbx):
        '''
        Will test that the function returns the expected result
        and that the DropBoxStorage function as been called with the expected parameters
        '''
        dbx.return_value = (['folder1'], ['file1', 'file2'])
        output = self.sut.listdir('Apps/')
        self.assertTupleEqual((['folder1'], ['file1', 'file2']), output)
        dbx.assert_called_once_with('Apps/')

    @patch('geonode.storage.dropbox.DropBoxStorage._open')
    def test_dropbox_open(self, dbx):
        '''
        Will test that the function returns the expected result
        and that the DropBoxStorage function as been called with the expected parameters
        '''
        dbx.return_value = io.StringIO()
        output = self.sut.open("name", mode='xx')
        self.assertEqual(type(output), io.StringIO().__class__)
        dbx.assert_called_once_with("name", 'xx')

    @patch('geonode.storage.dropbox.DropBoxStorage._full_path')
    def test_dropbox_path(self, dbx):
        '''
        Will test that the function returns the expected result
        and that the DropBoxStorage function as been called with the expected parameters
        '''
        dbx.return_value = "/opt/full/path/to/file"
        output = self.sut.path('file')
        self.assertEqual("/opt/full/path/to/file", output)
        dbx.assert_called_once_with('file')

    @patch('geonode.storage.dropbox.DropBoxStorage.save')
    def test_dropbox_save(self, dbx):
        '''
        Will test that the function returns the expected result
        and that the DropBoxStorage function as been called with the expected parameters
        '''
        dbx.return_value = "cleaned_name"
        output = self.sut.save('file_name', "content")
        self.assertEqual("cleaned_name", output)
        dbx.assert_called_once_with('file_name', "content")

    @patch('geonode.storage.dropbox.DropBoxStorage.size')
    def test_dropbox_size(self, dbx):
        '''
        Will test that the function returns the expected result
        and that the DropBoxStorage function as been called with the expected parameters
        '''
        dbx.return_value = 1
        output = self.sut.size('name')
        self.assertEqual(1, output)
        dbx.assert_called_once_with('name')


class TestGoogleStorageManager(SimpleTestCase):

    def setUp(self):
        self.sut = GoogleStorageManager

    @patch('storages.backends.gcloud.GoogleCloudStorage.delete')
    def test_google_deleted(self, gcs):
        '''
        Will test that the function returns the expected result
        and that the GoogleCloudStorage function as been called with the expected parameters
        '''
        gcs.return_value = None
        output = self.sut().delete('filename')
        self.assertIsNone(output)
        gcs.assert_called_once_with('filename')

    @patch('storages.backends.gcloud.GoogleCloudStorage.exists')
    def test_google_exists(self, gcs):
        '''
        Will test that the function returns the expected result
        and that the GoogleCloudStorage function as been called with the expected parameters
        '''
        gcs.return_value = True
        output = self.sut().exists('filename')
        self.assertTrue(output)
        gcs.assert_called_once_with('filename')

    @patch('storages.backends.gcloud.GoogleCloudStorage.listdir')
    def test_google_listdir(self, gcs):
        '''
        Will test that the function returns the expected result
        and that the GoogleCloudStorage function as been called with the expected parameters
        '''
        gcs.return_value = (['folder1'], ['file1', 'file2'])
        output = self.sut().listdir('Apps/')
        self.assertTupleEqual((['folder1'], ['file1', 'file2']), output)
        gcs.assert_called_once_with('Apps/')

    @patch('storages.backends.gcloud.GoogleCloudStorage._open')
    def test_google_open(self, gcs):
        '''
        Will test that the function returns the expected result
        and that the GoogleCloudStorage function as been called with the expected parameters
        '''
        gcs.return_value = io.StringIO()
        output = self.sut().open("name", mode='xx')
        self.assertEqual(type(output), io.StringIO().__class__)
        gcs.assert_called_once_with("name", 'xx')

    def test_google_path(self):
        '''
        Will test that the function returns the expected result
        and that the GoogleCloudStorage function as been called with the expected parameters
        '''
        with self.assertRaises(NotImplementedError):
            self.sut().path('file')

    @patch('storages.backends.gcloud.GoogleCloudStorage.save')
    def test_google_save(self, gcs):
        '''
        Will test that the function returns the expected result
        and that the GoogleCloudStorage function as been called with the expected parameters
        '''
        gcs.return_value = "cleaned_name"
        output = self.sut().save('file_name', "content")
        self.assertEqual("cleaned_name", output)
        gcs.assert_called_once_with('file_name', "content")

    @patch('storages.backends.gcloud.GoogleCloudStorage.size')
    def test_google_size(self, gcs):
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
    def test_aws_deleted(self, aws):
        '''
        Will test that the function returns the expected result
        and that the AwsStorageManager function as been called with the expected parameters
        '''
        aws.return_value = None
        output = self.sut().delete('filename')
        self.assertIsNone(output)
        aws.assert_called_once_with('filename')

    @patch('storages.backends.s3boto3.S3Boto3Storage.exists')
    def test_aws_exists(self, aws):
        '''
        Will test that the function returns the expected result
        and that the AwsStorageManager function as been called with the expected parameters
        '''
        aws.return_value = True
        output = self.sut().exists('filename')
        self.assertTrue(output)
        aws.assert_called_once_with('filename')

    @patch('storages.backends.s3boto3.S3Boto3Storage.listdir')
    def test_aws_listdir(self, aws):
        '''
        Will test that the function returns the expected result
        and that the AwsStorageManager function as been called with the expected parameters
        '''
        aws.return_value = (['folder1'], ['file1', 'file2'])
        output = self.sut().listdir('Apps/')
        self.assertTupleEqual((['folder1'], ['file1', 'file2']), output)
        aws.assert_called_once_with('Apps/')

    @patch('storages.backends.s3boto3.S3Boto3Storage._open')
    def test_aws_open(self, aws):
        '''
        Will test that the function returns the expected result
        and that the AwsStorageManager function as been called with the expected parameters
        '''
        aws.return_value = io.StringIO()
        output = self.sut().open("name", mode='xx')
        self.assertEqual(type(output), io.StringIO().__class__)
        aws.assert_called_once_with("name", 'xx')

    @patch('storages.backends.s3boto3.S3Boto3Storage._normalize_name')
    def test_aws_path(self, aws):
        '''
        Will test that the function returns the expected result
        and that the AwsStorageManager function as been called with the expected parameters
        '''
        aws.return_value = "/opt/full/path/to/file"
        output = self.sut().path('file')
        self.assertEqual("/opt/full/path/to/file", output)
        aws.assert_called_once_with('file')

    @patch('storages.backends.s3boto3.S3Boto3Storage.save')
    def test_aws_save(self, aws):
        '''
        Will test that the function returns the expected result
        and that the AwsStorageManager function as been called with the expected parameters
        '''
        aws.return_value = True
        output = self.sut().save('file_name', "content")
        self.assertTrue(output)
        aws.assert_called_once_with('file_name', "content")

    @patch('storages.backends.s3boto3.S3Boto3Storage.size')
    def test_aws_size(self, aws):
        '''
        Will test that the function returns the expected result
        and that the AwsStorageManager function as been called with the expected parameters
        '''
        aws.return_value = 1
        output = self.sut().size('name')
        self.assertEqual(1, output)
        aws.assert_called_once_with('name')


class TestStorageManager(TestCase):

    def setUp(self):
        self.sut = StorageManager
        self.project_root = os.path.abspath(os.path.dirname(__file__))

    @patch('django.core.files.storage.FileSystemStorage.delete')
    def test_storage_manager_deleted(self, strg):
        '''
        Will test that the function returns the expected result
        and that the StorageManager function as been called with the expected parameters
        '''
        strg.return_value = None
        output = self.sut().delete('filename')
        self.assertIsNone(output)
        strg.assert_called_once_with('filename')

    @patch('django.core.files.storage.FileSystemStorage.exists')
    def test_storage_manager_exists(self, strg):
        '''
        Will test that the function returns the expected result
        and that the StorageManager function as been called with the expected parameters
        '''
        strg.return_value = True
        output = self.sut().exists('filename')
        self.assertTrue(output)
        strg.assert_called_once_with('filename')

    @patch('django.core.files.storage.FileSystemStorage.listdir')
    def test_storage_manager_listdir(self, strg):
        '''
        Will test that the function returns the expected result
        and that the StorageManager function as been called with the expected parameters
        '''
        strg.return_value = (['folder1'], ['file1', 'file2'])
        output = self.sut().listdir('Apps/')
        self.assertTupleEqual((['folder1'], ['file1', 'file2']), output)
        strg.assert_called_once_with('Apps/')

    @patch('django.core.files.storage.FileSystemStorage._open')
    def test_storage_manager_open(self, strg):
        '''
        Will test that the function returns the expected result
        and that the StorageManager function as been called with the expected parameters
        '''
        strg.return_value = io.StringIO()
        output = self.sut().open("name", mode='xx')
        self.assertEqual(type(output), io.StringIO().__class__)
        strg.assert_called_once()

    @patch('django.core.files.storage.FileSystemStorage.path')
    def test_storage_manager_path(self, strg):
        '''
        Will test that the function returns the expected result
        and that the StorageManager function as been called with the expected parameters
        '''
        strg.return_value = "/opt/full/path/to/file"
        output = self.sut().path('file')
        self.assertEqual("/opt/full/path/to/file", output)
        strg.assert_called_once_with('file')

    @patch('django.core.files.storage.FileSystemStorage.save')
    def test_storage_manager_save(self, strg):
        '''
        Will test that the function returns the expected result
        and that the StorageManager function as been called with the expected parameters
        '''
        strg.return_value = True
        output = self.sut().save('file_name', "content")
        self.assertTrue(output)
        strg.assert_called_once()

    @patch('django.core.files.storage.FileSystemStorage.size')
    def test_storage_manager_size(self, strg):
        '''
        Will test that the function returns the expected result
        and that the StorageManager function as been called with the expected parameters
        '''
        strg.return_value = 1
        output = self.sut().size('name')
        self.assertEqual(1, output)
        strg.assert_called_once_with('name')

    # @patch('django.core.files.storage.FileSystemStorage.save')
    # @patch('django.core.files.storage.FileSystemStorage.path')
    def test_storage_manager_replace_files_list(self):  # , path, strg):
        '''
        Will test that the function returns the expected result
        and that the StorageManager function as been called with the expected parameters
        '''
        # path.return_value = '/opt/full/path/to/file'
        # strg.return_value = '/opt/full/path/to/file'
        old_files = ['/opt/full/path/to/file', '/opt/full/path/to/file']
        new_files = [os.path.join(f"{self.project_root}", "tests/data/test_sld.sld"), os.path.join(f"{self.project_root}", "tests/data/test_data.json")]
        dataset = create_single_dataset('storage_manager')
        dataset.files = old_files
        dataset.save()
        output = self.sut().replace(dataset, new_files)
        self.assertEqual(2, len(output['files']))
        self.assertTrue('file.sld' in output['files'][0])
        self.assertTrue('file.json' in output['files'][1])

    @patch('django.core.files.storage.FileSystemStorage.save')
    @patch('django.core.files.storage.FileSystemStorage.path')
    def test_storage_manager_replace_single_file(self, path, strg):
        '''
        Will test that the function returns the expected result
        and that the StorageManager function as been called with the expected parameters
        '''
        path.return_value = '/opt/full/path/to/file'
        strg.return_value = '/opt/full/path/to/file'
        expected = '/opt/full/path/to/file'
        dataset = create_single_dataset('storage_manager')
        dataset.files = ['/opt/full/path/to/file2']
        dataset.save()
        with open('geonode/base/fixtures/test_sld.sld') as new_file:
            output = self.sut().replace(dataset, new_file)
        self.assertListEqual([expected], output['files'])


class TestDataRetriever(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.project_root = os.path.abspath(os.path.dirname(__file__))

    def setUp(self):
        self.sut = StorageManager
        self.local_files_paths = {
            "base_file": f"{gisdata.GOOD_DATA}/vector/single_point.shp",
            "dbf_file": f"{gisdata.GOOD_DATA}/vector/single_point.dbf",
            "shx_file": f"{gisdata.GOOD_DATA}/vector/single_point.shx",
            "prj_file": f"{gisdata.GOOD_DATA}/vector/single_point.prj",
        }
        github_path = "https://github.com/GeoNode/gisdata/tree/master/gisdata/data/good/vector/"
        self.remote_files = {
            "base_file": f"{github_path}/single_point.shp",
            "dbf_file": f"{github_path}/single_point.dbf",
            "shx_file": f"{github_path}/single_point.shx",
            "prj_file": f"{github_path}/single_point.prj",
        }
        return super().setUp()

    def test_file_are_not_transfered_local(self):
        _obj = self.sut(remote_files=self.local_files_paths)
        self.assertTrue(hasattr(_obj, "data_retriever"))
        self.assertIsNone(_obj.data_retriever.temporary_folder)

    def test_clone_remote_files_local(self):
        storage_manager = self.sut(remote_files=self.local_files_paths)
        storage_manager.clone_remote_files()
        expected_file_set = {
            'single_point.shx',
            'single_point.prj',
            'single_point.dbf',
            'single_point.shp'
        }
        self.assertIsNotNone(storage_manager.data_retriever.temporary_folder)
        _files = os.listdir(storage_manager.data_retriever.temporary_folder)
        self.assertSetEqual(expected_file_set, set(_files))

    def test_get_retrieved_paths_local(self):
        self.maxDiff = None
        storage_manager = self.sut(remote_files=self.local_files_paths)
        # get_retrieved_paths should not transfer the remote paths
        with self.assertRaises(DataRetrieverExcepion):
            storage_manager.get_retrieved_paths()

        # instead first is needed to clone the remove files and then take the paths
        storage_manager.clone_remote_files()
        files = storage_manager.get_retrieved_paths()

        expected_sorted_list = [
            ('base_file', f'{storage_manager.data_retriever.temporary_folder}/single_point.shp'),
            ('dbf_file', f'{storage_manager.data_retriever.temporary_folder}/single_point.dbf'),
            ('prj_file', f'{storage_manager.data_retriever.temporary_folder}/single_point.prj'),
            ('shx_file', f'{storage_manager.data_retriever.temporary_folder}/single_point.shx')
        ]
        self.assertIsNotNone(storage_manager.data_retriever.temporary_folder)
        self.assertListEqual(expected_sorted_list, sorted(files.items()))

    def test_delete_retrieved_paths_local(self):
        self.maxDiff = None
        storage_manager = self.sut(remote_files=self.local_files_paths)
        # instead first is needed to clone the remove files and then take the paths
        storage_manager.clone_remote_files()
        expected_file_set = {
            'single_point.shx',
            'single_point.prj',
            'single_point.dbf',
            'single_point.shp'
        }
        _tmp_folder_path = storage_manager.data_retriever.temporary_folder
        self.assertIsNotNone(_tmp_folder_path)
        _files = os.listdir(storage_manager.data_retriever.temporary_folder)
        # check the file exists in the temporary folder so we can be sure that the delete works
        self.assertSetEqual(expected_file_set, set(_files))

        storage_manager.delete_retrieved_paths(force=True)
        self.assertIsNone(storage_manager.data_retriever.temporary_folder)
        # the directory does not exists
        self.assertFalse(os.path.exists(_tmp_folder_path))

    def test_file_are_not_transfered_remote(self):
        _obj = self.sut(remote_files=self.remote_files)
        self.assertTrue(hasattr(_obj, "data_retriever"))
        self.assertIsNone(_obj.data_retriever.temporary_folder)

    def test_clone_remote_files_remote(self):
        storage_manager = self.sut(remote_files=self.remote_files)
        storage_manager.clone_remote_files()
        expected_file_set = {
            'single_point.shx',
            'single_point.prj',
            'single_point.dbf',
            'single_point.shp'
        }
        self.assertIsNotNone(storage_manager.data_retriever.temporary_folder)
        _files = os.listdir(storage_manager.data_retriever.temporary_folder)
        self.assertSetEqual(expected_file_set, set(_files))

    def test_get_retrieved_paths_remote(self):
        self.maxDiff = None
        storage_manager = self.sut(remote_files=self.remote_files)
        # get_retrieved_paths should not transfer the remote paths
        with self.assertRaises(DataRetrieverExcepion):
            storage_manager.get_retrieved_paths()

        # instead first is needed to clone the remove files and then take the paths
        storage_manager.clone_remote_files()
        files = storage_manager.get_retrieved_paths()

        expected_sorted_list = [
            ('base_file', f'{storage_manager.data_retriever.temporary_folder}/single_point.shp'),
            ('dbf_file', f'{storage_manager.data_retriever.temporary_folder}/single_point.dbf'),
            ('prj_file', f'{storage_manager.data_retriever.temporary_folder}/single_point.prj'),
            ('shx_file', f'{storage_manager.data_retriever.temporary_folder}/single_point.shx')
        ]
        self.assertIsNotNone(storage_manager.data_retriever.temporary_folder)
        self.assertListEqual(expected_sorted_list, sorted(files.items()))

    def test_delete_retrieved_paths_remote(self):
        self.maxDiff = None
        storage_manager = self.sut(remote_files=self.remote_files)
        # instead first is needed to clone the remove files and then take the paths
        storage_manager.clone_remote_files()
        expected_file_set = {
            'single_point.shx',
            'single_point.prj',
            'single_point.dbf',
            'single_point.shp'
        }
        _tmp_folder_path = storage_manager.data_retriever.temporary_folder
        self.assertIsNotNone(_tmp_folder_path)
        _files = os.listdir(storage_manager.data_retriever.temporary_folder)
        # check the file exists in the temporary folder so we can be sure that the delete works
        self.assertSetEqual(expected_file_set, set(_files))

        storage_manager.delete_retrieved_paths(force=True)
        self.assertIsNone(storage_manager.data_retriever.temporary_folder)
        # the directory does not exists
        self.assertFalse(os.path.exists(_tmp_folder_path))

    def test_storage_manager_rmtree(self):
        '''
        Will test that the rmtree function works as expected
        '''
        _dirs = [
            'subdir1',
            'subdir2',
            'subdir1/subsubdir1'
        ]
        _files = [
            'subdir1/tmp_file1',
            'subdir1/tmp_file2',
            'subdir2/tmp_file2',
            'subdir1/subsubdir1/tmp_file11'
        ]
        _tmpdir = mkdtemp()

        for _dir in _dirs:
            if not os.path.exists(os.path.join(_tmpdir, _dir)):
                os.makedirs(os.path.join(_tmpdir, _dir), exist_ok=True)
            self.assertTrue(os.path.exists(os.path.join(_tmpdir, _dir)))
            self.assertTrue(os.path.isdir(os.path.join(_tmpdir, _dir)))

        for _file in _files:
            with open(os.path.join(_tmpdir, _file), 'wb+'):
                pass
            self.assertTrue(os.path.exists(os.path.join(_tmpdir, _file)))
            self.assertTrue(os.path.isfile(os.path.join(_tmpdir, _file)))

        self.sut().rmtree(_tmpdir)
        self.assertFalse(os.path.exists(_tmpdir))

    def test_zip_file_should_correctly_recognize_main_extension_with_csv(self):
        # reinitiate the storage manager with the zip file
        storage_manager = self.sut(remote_files={"base_file": os.path.join(f"{self.project_root}", "tests/data/example.zip")})
        storage_manager.clone_remote_files()

        self.assertIsNotNone(storage_manager.data_retriever.temporary_folder)
        _files = storage_manager.get_retrieved_paths()
        self.assertTrue("example.csv" in _files.get("base_file"))

    def test_zip_file_should_correctly_recognize_main_extension_with_shp(self):
        # zipping files
        storage_manager = self.sut(remote_files=self.local_files_paths)
        storage_manager.clone_remote_files()
        storage_manager.data_retriever.temporary_folder
        output = shutil.make_archive(f"{storage_manager.data_retriever.temporary_folder}/output", 'zip', storage_manager.data_retriever.temporary_folder)
        # reinitiate the storage manager with the zip file
        storage_manager = self.sut(remote_files={"base_file": output})
        storage_manager.clone_remote_files()

        self.assertIsNotNone(storage_manager.data_retriever.temporary_folder)
        _files = storage_manager.get_retrieved_paths()
        self.assertTrue("single_point.shp" in _files.get("base_file"))
