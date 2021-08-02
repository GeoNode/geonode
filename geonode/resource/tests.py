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
import tempfile
import shutil
import os

from uuid import uuid1
from unittest.mock import patch
from django.conf import settings

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from geonode.base.populate_test_data import create_models
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.resource.manager import ResourceManager
from geonode.base.models import ResourceBase
from geonode.documents.models import Document
from geonode.layers.models import Dataset
from geonode.base.populate_test_data import create_single_doc, create_single_dataset, create_single_map
from geonode.layers.populate_datasets_data import create_dataset_data
from geonode.maps.models import MapLayer
from geonode.services.models import Service, HarvestJob

from pinax.ratings.models import OverallRating


class ResourceManagerClassTest:
    pass


class TestResourceManager(GeoNodeBaseTestSupport):
    def setUp(self):
        create_models(b'dataset')
        create_models(b'map')
        create_models(b'document')
        User = get_user_model()
        self.user = User.objects.create(username='test', email='test@test.com')
        self.rm = ResourceManager()

    # @patch('os.environ.get', return_value='geonode.resource.tests.ResourceManagerClassTest')
    # def test_get_concrete_manager(self, mock_get):
    #     self.assertEqual(self.rm._concrete_resource_manager.__class__.__name__, 'ResourceManagerClassTest')

    def test__get_instance(self):
        # test with invalid object
        self.assertIsNone(self.rm._get_instance('invalid_uuid'))
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
        dt = Dataset.objects.filter(uuid__isnull=False).exclude(uuid='').first()
        self.assertFalse(self.rm.exists('invalid_uuid'))
        self.assertTrue(self.rm.exists(dt.uuid))
        self.assertTrue(self.rm.exists("invalid_id", instance=dt))

    def test_delete(self):
        doc = create_single_doc("test_delete_doc")
        dt = create_single_dataset("test_delete_dataset")
        map = create_single_map("test_delete_dataset")
        geonode_service = Service.objects.create(
                base_url="http://fake_test",
                owner=self.user)
        HarvestJob.objects.create(
            service=geonode_service,
            resource_id=dt.id
        )
        # Add dataset to a map
        MapLayer.objects.create(map=map, name=dt.alternate, stack_order=1).save()
        # Create the rating for dataset
        OverallRating.objects.create(
            category=2,
            object_id=dt.id,
            content_type=ContentType.objects.get(model='dataset'),
            rating=3)
        create_dataset_data(dt.resourcebase_ptr_id)
        res = self.rm.delete(doc.uuid, instance=doc)
        self.assertTrue(res)
        # Before dataset delete
        self.assertEqual(MapLayer.objects.filter(name='geonode:test_delete_dataset').count(), 1)
        self.assertEqual(OverallRating.objects.filter(object_id=dt.id).count(), 1)
        # try deleting with no default style, havest_job withalternate as resource_id, with uploads
        # TODO
        res = self.rm.delete(dt.uuid, instance=dt)
        self.assertTrue(res)

        # After dataset delete
        self.assertEqual(MapLayer.objects.filter(name='geonode:test_delete_dataset').count(), 0)
        self.assertEqual(OverallRating.objects.filter(object_id=dt.id).count(), 0)

    def test_create(self):
        dt = Dataset.objects.filter(uuid__isnull=False).exclude(uuid='').first()
        dataset_defaults = {"owner": self.user, "title": "test_create_dataset"}
        with self.assertRaises(ValidationError):
            res = self.rm.create(dt.uuid, resource_type=Dataset)
        new_uuid = str(uuid1())
        res = self.rm.create(new_uuid, resource_type=Dataset, defaults=dataset_defaults)
        self.assertEqual(res, Dataset.objects.get(uuid=new_uuid))

    def test_update(self):
        dt = create_single_dataset("test_update_dataset")
        vals = {
            "name": "new_name_test_update_dataset"
        }
        res = self.rm.update(dt.uuid, vals=vals, keywords=["testing"], regions=["not_known", "Africa"])
        self.assertIn("Africa", res.regions.values_list("name", flat=True))
        self.assertTrue(all(x in res.keywords.values_list("name", flat=True) for x in ["testing", "not_known"]))
        self.assertEqual(res.name, vals["name"])
        # TODO test metadatauploaded and xml file

    def test_ingest(self):
        doc_files = [f"{settings.MEDIA_ROOT}/img.gif"]
        dt_files = ['/opt/full/path/to/file', '/opt/full/path/to/file']
        defaults = {"owner": self.user}
        # raises an exception if resource_type is not provided
        with self.assertRaises((Exception, AttributeError)):
            self.rm.ingest(dt_files)
        # ingest with documents
        res = self.rm.ingest(dt_files, resource_type=Document, defaults=defaults)
        self.assertTrue(isinstance(res, Document))
        # ingest with datasets
        # res = self.rm.ingest(dt_files, resource_type=Dataset, defaults=defaults)
        # self.assertTrue(isinstance(res, Dataset))

    def test_copy(self):
        dt = create_single_dataset("test_copy_dataset")
        # test with no reference object provided
        self.assertIsNone(self.rm.copy(None))
        # test with existing uuid
        # with self.assertRaises((Exception, AttributeError)):
        res = self.rm.copy(dt)
        self.assertEqual(res.perms, dt.perms)

    @patch.object(ResourceManager, '_validate_resource')
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

    @patch.object(ResourceManager, '_validate_resource')
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
        # self.assertTrue(self.rm._validate_resource(map, action_type="replace"))
        with self.assertRaises(ObjectDoesNotExist):
            # TODO In function rais this only when object is not found
            self.rm._validate_resource(dt, action_type="invalid")

    def test_exec(self):
        dt = create_single_dataset("san_andres_y_providencia")
        map = create_single_map("test_exec_map")
        #  mock_rm.set_style.return_value = dt
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
        perm_spec = {"users": {"test": ['view_resourcebase', 'change_resourcebase']}, "groups": {}}
