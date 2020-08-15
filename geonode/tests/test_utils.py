from datetime import datetime, timedelta
from unittest.mock import patch

from geonode.br.management.commands.utils.utils import ignore_time
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.utils import copy_tree


class TestCopyTree(GeoNodeBaseTestSupport):
    @patch('shutil.copy2')
    @patch('os.path.getmtime', return_value=(datetime.now() - timedelta(days=1)).timestamp())
    @patch('os.listdir', return_value=['Erling_Haaland.jpg'])
    @patch('os.path.isdir', return_value=False)
    def test_backup_of_root_files_with_modification_dates_meeting_less_than_filter_criteria(
            self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copy2):
        """
        Test that all root directories whose modification dates meet the 'data_dt_filter'
        less-than iso timestamp are backed-up successfully
        """
        copy_tree('/src', '/dst', ignore=ignore_time('<', datetime.now().isoformat()))
        self.assertTrue(patch_shutil_copy2.called)

    @patch('shutil.copy2')
    @patch('os.path.getmtime', return_value=(datetime.now() + timedelta(days=1)).timestamp())
    @patch('os.listdir', return_value=['Sancho.jpg'])
    @patch('os.path.isdir', return_value=False)
    def test_skipped_backup_of_root_files_with_modification_dates_not_meeting_less_than_filter_criteria(
            self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copy2):
        """
        Test that all root directories whose modification dates do not meet the 'data_dt_filter'
        less-than iso timestamp are not backed-up
        """
        copy_tree('/src', '/dst', ignore=ignore_time('<', datetime.now().isoformat()))
        self.assertFalse(patch_shutil_copy2.called)

    @patch('shutil.copy2')
    @patch('os.path.getmtime', return_value=(datetime.now() - timedelta(days=1)).timestamp())
    @patch('os.listdir', return_value=['Saala.jpg'])
    @patch('os.path.isdir', return_value=False)
    def test_backup_of_root_files_with_modification_dates_meeting_greater_than_filter_criteria(
            self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copy2):
        """
        Test that all root directories whose modification dates do not meet the 'data_dt_filter'
        greater-than iso timestamp are backed-up successfully
        """
        copy_tree('/src', '/dst', ignore=ignore_time('>', datetime.now().isoformat()))
        self.assertFalse(patch_shutil_copy2.called)

    @patch('shutil.copy2')
    @patch('os.path.getmtime', return_value=(datetime.now() + timedelta(days=1)).timestamp())
    @patch('os.listdir', return_value=['Sadio.jpg'])
    @patch('os.path.isdir', return_value=False)
    def test_skipped_backup_of_root_files_with_modification_dates_not_meeting_greater_than_filter_criteria(
            self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copy2):
        """
        Test that all root directories whose modification dates do not meet the 'data_dt_filter'
        less-than iso timestamp are not backed-up
        """
        copy_tree('/src', '/dst', ignore=ignore_time('>', datetime.now().isoformat()))
        self.assertTrue(patch_shutil_copy2.called)

    @patch('os.path.exists', return_value=True)
    @patch('shutil.copytree')
    @patch('os.path.getmtime', return_value=0)
    @patch('os.listdir', return_value=['an_awesome_directory'])
    @patch('os.path.isdir', return_value=True)
    def test_backup_of_child_directories(
            self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copytree, path_os_exists):
        """
        Test that all directories which meet the 'ignore criteria are backed-up'
        """
        copy_tree('/src', '/dst', ignore=ignore_time('>=', datetime.now().isoformat()))
        self.assertTrue(patch_shutil_copytree.called)
