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
import io
import os

from uuid import uuid4
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from geonode.groups.models import GroupProfile
from geonode.base.populate_test_data import create_models
from geonode.resource.utils import resourcebase_post_save
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.resource.manager import ResourceManager
from geonode.base.models import LinkedResource, ResourceBase
from geonode.layers.models import Dataset
from geonode.services.models import Service
from geonode.documents.models import Document
from geonode.maps.models import Map, MapLayer
from geonode.resource import settings as rm_settings
from geonode.layers.populate_datasets_data import create_dataset_data
from geonode.base.populate_test_data import create_single_doc, create_single_map, create_single_dataset
from geonode.thumbs.utils import ThumbnailAlgorithms

from gisdata import GOOD_DATA


class ResourceManagerClassTest:
    pass


class TestResourceManager(GeoNodeBaseTestSupport):
    def setUp(self):
        create_models(b"dataset")
        create_models(b"map")
        create_models(b"document")
        User = get_user_model()
        self.user = User.objects.create(username="test", email="test@test.com")
        self.rm = ResourceManager()

    def test_get_concrete_manager(self):
        original_r_m_c_c = rm_settings.RESOURCE_MANAGER_CONCRETE_CLASS
        # mock class
        rm_settings.RESOURCE_MANAGER_CONCRETE_CLASS = "geonode.resource.tests.ResourceManagerClassTest"
        rm = ResourceManager()
        self.assertEqual(rm._concrete_resource_manager.__class__.__name__, "ResourceManagerClassTest")
        # re assign class to original
        rm_settings.RESOURCE_MANAGER_CONCRETE_CLASS = original_r_m_c_c

    def test__get_instance(self):
        # test with invalid object
        self.assertIsNone(self.rm._get_instance("invalid_uuid"))
        # Test with valid object
        self.assertIsNotNone(self.rm._get_instance(ResourceBase.objects.first().uuid))

    def test_search(self):
        # test with no specific resource_type provided
        result = self.rm.search({"title__icontains": "ipsum", "abstract__icontains": "ipsum"}, resource_type=None)
        self.assertEqual(result.count(), 3)
        # test with specific resource_type
        result = self.rm.search({"title__icontains": "ipsum", "abstract__icontains": "ipsum"}, resource_type=Document)
        self.assertEqual(result.count(), 2)

    def test_exists(self):
        dt = Dataset.objects.filter(uuid__isnull=False).exclude(uuid="").first()
        self.assertFalse(self.rm.exists("invalid_uuid"))
        self.assertTrue(self.rm.exists(dt.uuid))
        self.assertTrue(self.rm.exists("invalid_id", instance=dt))

    def test_delete(self):
        doc = create_single_doc("test_delete_doc")
        dt = create_single_dataset("test_delete_dataset")
        map = create_single_map("test_delete_dataset")
        Service.objects.create(base_url="http://fake_test", owner=self.user)

        # Add dataset to a map
        MapLayer.objects.create(map=map, name=dt.alternate).save()
        # Create the rating for dataset
        create_dataset_data(dt.resourcebase_ptr_id)
        res = self.rm.delete(doc.uuid, instance=doc)
        self.assertTrue(res)
        res = self.rm.delete(dt.uuid, instance=dt)
        self.assertTrue(res)
        # After dataset delete
        self.assertEqual(MapLayer.objects.filter(name="geonode:test_delete_dataset").count(), 0)

    def test_create(self):
        dt = Dataset.objects.filter(uuid__isnull=False).exclude(uuid="").first()
        dataset_defaults = {"owner": self.user, "title": "test_create_dataset"}
        res = self.rm.create(dt.uuid, resource_type=Dataset)
        new_uuid = str(uuid4())
        res = self.rm.create(new_uuid, resource_type=Dataset, defaults=dataset_defaults)
        self.assertEqual(res, Dataset.objects.get(uuid=new_uuid))

    def test_update(self):
        dt = create_single_dataset("test_update_dataset")
        vals = {"name": "new_name_test_update_dataset"}
        res = self.rm.update(dt.uuid, vals=vals, keywords=["testing"], regions=["not_known", "Africa"])
        self.assertIn("Africa", res.regions.values_list("name", flat=True))
        self.assertTrue(all(x in res.keywords.values_list("name", flat=True) for x in ["testing", "not_known"]))
        self.assertEqual(res.name, vals["name"])
        # TODO test metadatauploaded and xml file

    def test_ingest(self):
        dt_files = [os.path.join(GOOD_DATA, "raster", "relief_san_andres.tif")]

        # ingest with documents
        res = self.rm.create(
            None,
            resource_type=Document,
            defaults=dict(owner=self.user, files=dt_files),
        )
        self.assertTrue(isinstance(res, Document))
        res.delete()
        # ingest with datasets
        res = self.rm.create(
            None,
            resource_type=Dataset,
            defaults=dict(owner=self.user, files=dt_files),
        )
        self.assertTrue(isinstance(res, Dataset))
        res.delete()

    def test_dataset_copy(self):
        def _copy_assert_resource(res, title):
            dataset_copy = None
            try:
                dataset_copy = self.rm.copy(res, defaults=dict(title=title))
                self.assertIsNotNone(dataset_copy)
                self.assertEqual(dataset_copy.title, title)
            finally:
                if dataset_copy:
                    dataset_copy.delete()
                self.assertIsNotNone(res)
                res.delete()

        self.client.login(username="admin", password="admin")
        dt_files = [os.path.join(GOOD_DATA, "raster", "relief_san_andres.tif")]

        # copy with documents
        res = self.rm.create(
            None,
            resource_type=Document,
            defaults={
                "title": "relief_san_andres",
                "owner": self.user,
                "extension": "tif",
                "data_title": "relief_san_andres",
                "data_type": "tif",
                "files": dt_files,
            },
        )
        self.assertTrue(isinstance(res, Document))
        _copy_assert_resource(res, "Testing Document 2")

        # copy with datasets
        res = self.rm.create(
            None,
            resource_type=Dataset,
            defaults={
                "owner": self.user,
                "title": "Testing Dataset",
                "data_title": "relief_san_andres",
                "data_type": "tif",
                "files": dt_files,
            },
        )
        self.assertTrue(isinstance(res, Dataset))
        _copy_assert_resource(res, "Testing Dataset 2")

        # copy with maps
        res = create_single_map("A Test Map")
        self.assertTrue(isinstance(res, Map))
        _copy_assert_resource(res, "A Test Map 2")

    def test_resource_copy_with_linked_resources(self):
        def _copy_assert_resource(res, title):
            dataset_copy = None
            try:
                dataset_copy = self.rm.copy(res, defaults=dict(title=title))
                self.assertIsNotNone(dataset_copy)
                self.assertEqual(dataset_copy.title, title)
            finally:
                if dataset_copy:
                    dataset_copy.delete()
                self.assertIsNotNone(res)
                res.delete()

        # copy with maps
        res = create_single_map("A Test Map")
        target = ResourceBase.objects.first()
        LinkedResource.objects.get_or_create(source_id=res.id, target_id=target.id)
        self.assertTrue(isinstance(res, Map))
        _copy_assert_resource(res, "A Test Map 2")

    @patch.object(ResourceManager, "_validate_resource")
    def test_append(self, mock_validator):
        mock_validator.return_value = True
        dt = create_single_dataset("test_append_dataset")
        # Before append
        self.assertEqual(dt.name, "test_append_dataset")
        # After append
        self.rm.append(dt, vals={"name": "new_name_test_append_dataset"})
        self.assertEqual(dt.name, "new_name_test_append_dataset")
        # test with failing validator
        mock_validator.return_value = False
        self.rm.append(dt, vals={"name": "new_name2"})
        self.assertEqual(dt.name, "new_name_test_append_dataset")

    @patch.object(ResourceManager, "_validate_resource")
    def test_replace(self, mock_validator):
        dt = create_single_dataset("test_replace_dataset")
        mock_validator.return_value = True
        self.rm.replace(dt, vals={"name": "new_name_test_replace_dataset"})
        self.assertEqual(dt.name, "new_name_test_replace_dataset")
        # test with failing validator
        mock_validator.return_value = False
        self.rm.replace(dt, vals={"name": "new_name2"})
        self.assertEqual(dt.name, "new_name_test_replace_dataset")

    def test_validate_resource(self):
        doc = create_single_doc("test_delete_doc")
        dt = create_single_dataset("test_delete_dataset")
        map = create_single_map("test_delete_dataset")
        with self.assertRaises(Exception):
            # append is for only datasets
            self.rm._validate_resource(doc, action_type="append")
        self.assertTrue(self.rm._validate_resource(doc, action_type="replace"))
        self.assertTrue(self.rm._validate_resource(dt, action_type="replace"))
        self.assertTrue(self.rm._validate_resource(map, action_type="replace"))
        with self.assertRaises(ObjectDoesNotExist):
            # TODO In function rais this only when object is not found
            self.rm._validate_resource(dt, action_type="invalid")

    def test_exec(self):
        map = create_single_map("test_exec_map")
        self.assertIsNone(self.rm.exec("set_style", None, instance=None))
        self.assertEqual(self.rm.exec("set_style", map.uuid, instance=map), map)

    def test_remove_permissions(self):
        with self.settings(DEFAULT_ANONYMOUS_VIEW_PERMISSION=True):
            dt = create_single_dataset("test_dataset")
            map = create_single_map("test_exec_map")
            self.assertFalse(self.rm.remove_permissions("invalid", instance=None))
            self.assertTrue(self.rm.remove_permissions(map.uuid, instance=map))
            self.assertTrue(self.rm.remove_permissions(dt.uuid, instance=dt))

    def test_set_permissions(self):
        norman = get_user_model().objects.get(username="norman")
        anonymous = get_user_model().objects.get(username="AnonymousUser")
        doc = create_single_doc("test_delete_doc")
        map = create_single_map("test_delete_dataset")
        dt = create_single_dataset("test_delete_dataset")
        public_group, _public_created = GroupProfile.objects.get_or_create(
            slug="public_group", title="public_group", access="public"
        )
        private_group, _private_created = GroupProfile.objects.get_or_create(
            slug="private_group", title="private_group", access="private"
        )

        perm_spec = {
            "users": {
                "AnonymousUser": ["change_dataset_style", "view_resourcebase"],
                "norman": ["view_resourcebase", "change_dataset_style"],
            },
            "groups": {
                "public_group": ["view_resourcebase"],
                "private_group": ["view_resourcebase", "change_resourcebase"],
            },
        }
        self.assertTrue(self.rm.set_permissions(dt.uuid, instance=dt, permissions=perm_spec))
        self.assertFalse(self.rm.set_permissions("invalid_uuid", instance=None, permissions=perm_spec))
        # Test permissions assigned
        self.assertTrue(norman.has_perm("change_dataset_style", dt))
        self.assertFalse(norman.has_perm("change_resourcebase", dt.get_self_resource()))
        # Test with no specified permissions
        with patch("geonode.security.utils.skip_registered_members_common_group") as mock_v:
            mock_v.return_value = True
            with self.settings(DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION=False, DEFAULT_ANONYMOUS_VIEW_PERMISSION=False):
                self.assertTrue(self.rm.remove_permissions(dt.uuid, instance=dt))
                self.assertFalse(anonymous.has_perm("view_resourcebase", dt.get_self_resource()))
                self.assertFalse(anonymous.has_perm("download_resourcebase", dt.get_self_resource()))
        # Test "download" permissions retention policy
        perm_spec = {
            "users": {
                "AnonymousUser": ["view_resourcebase", "download_resourcebase"],
                "norman": ["view_resourcebase", "download_resourcebase"],
            },
            "groups": {
                "public_group": ["view_resourcebase", "download_resourcebase"],
                "private_group": ["view_resourcebase", "download_resourcebase", "change_resourcebase"],
            },
        }
        # 1. "download" permissions are allowed on "Datasets"
        self.assertTrue(self.rm.set_permissions(dt.uuid, instance=dt, permissions=perm_spec))
        self.assertTrue(norman.has_perm("download_resourcebase", dt.get_self_resource()))
        # 2. "download" permissions are allowed on "Documents"
        self.assertTrue(self.rm.set_permissions(doc.uuid, instance=doc, permissions=perm_spec))
        self.assertTrue(norman.has_perm("download_resourcebase", doc.get_self_resource()))
        # 3. "download" permissions are NOT allowed on "Maps"
        self.assertTrue(self.rm.set_permissions(map.uuid, instance=map, permissions=perm_spec))
        self.assertFalse(norman.has_perm("download_resourcebase", map.get_self_resource()))

    def test_set_thumbnail(self):
        doc = create_single_doc("test_thumb_doc")
        dt = create_single_dataset("test_thumb_dataset")
        self.assertFalse(self.rm.set_thumbnail("invalid_uuid"))
        self.assertTrue(self.rm.set_thumbnail(dt.uuid, instance=dt))
        self.assertTrue(self.rm.set_thumbnail(doc.uuid, instance=doc))

    def test_set_thumbnail_algo(self):
        thumb_path = os.path.join(os.path.dirname(__file__), "../tests/data/thumb_sample.png")
        image = io.open(thumb_path, "rb").read()
        doc = create_single_doc("test_thumb_doc")

        self.assertTrue(self.rm.set_thumbnail(doc.uuid, instance=doc), "Error in using default image algo")
        self.assertTrue(
            self.rm.set_thumbnail(doc.uuid, instance=doc, thumbnail=image, thumbnail_algorithm=ThumbnailAlgorithms.fit),
            "Error in using FIT image algo",
        )
        self.assertTrue(
            self.rm.set_thumbnail(
                doc.uuid, instance=doc, thumbnail=image, thumbnail_algorithm=ThumbnailAlgorithms.scale
            ),
            "Error in using SCALE image algo",
        )


class TestResourcebasePostSave(GeoNodeBaseTestSupport):
    @patch("geonode.resource.utils.call_storers")
    def test_resourcebase_post_save(self, mock_call_storers):
        """
        Test the custom dict is correctly handled if passed as expected
        """

        instance = create_single_dataset(name="storer_db")
        kwargs = {"custom": [1, 2, 3]}

        mock_call_storers.return_value = instance

        resourcebase_post_save(instance=instance, **kwargs)

        mock_call_storers.assert_called_with(instance, kwargs["custom"])

        instance.delete()

    @patch("geonode.resource.utils.call_storers")
    def test_resourcebase_post_save_raise_error(self, mock_call_storers):
        """
        Test the custom dict is ignored if not correctly passed
        """

        instance = create_single_dataset(name="storer_db")
        kwargs = {"key": [1, 2, 3]}

        mock_call_storers.return_value = instance

        resourcebase_post_save(instance=instance, **kwargs)

        with self.assertRaises(Exception):
            mock_call_storers.assert_called_with(instance, kwargs["custom"])

        instance.delete()

    @patch("geonode.resource.utils.call_storers")
    def test_resource_manager_update_should_handle_customs(self, mock_call_storers):
        """
        If custom payload is correctly applied, the storer will update the data
        """
        from geonode.resource.manager import resource_manager

        instance = create_single_dataset(name="storer_db")

        mock_call_storers.return_value = instance

        self.custom = {"uuid": "abc123cfde", "name": "updated name"}

        resource_manager.update(str(instance.uuid), instance=instance, custom=self.custom)
        mock_call_storers.assert_called_with(instance, self.custom)

        instance.delete()
