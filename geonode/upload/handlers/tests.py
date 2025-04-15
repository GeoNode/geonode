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
from django.test import TestCase
from geonode.base.populate_test_data import create_single_dataset
from django.contrib.auth import get_user_model
from dynamic_models.models import ModelSchema
from geonode.upload.handlers.utils import (
    create_alternate,
    drop_dynamic_model_schema,
    should_be_imported,
)
from geonode.upload.handlers.base import BaseHandler


class TestHandlersUtils(TestCase):
    databases = ("default", "datastore")

    def test_should_be_imported_return_true(self):
        """
        Should return true because a dataset with the same name for the user
        already exsits, but was not asked to skip the existing
        """
        user, _ = get_user_model().objects.get_or_create(username="admin")
        dataset = create_single_dataset(name="single_dataset", owner=user)
        result = should_be_imported(layer=dataset.name, user=user)
        self.assertTrue(result)

    def test_should_be_imported_return_true_with_no_dataset(self):
        """
        Return True because the dataset does not exists
        """
        user, _ = get_user_model().objects.get_or_create(username="admin")
        result = should_be_imported(layer="dataset_name", user=user)
        self.assertTrue(result)

    def test_should_be_imported_return_false(self):
        """
        Should return false because a dataset with the same name for the user
        already exsits and is required to skipt the existing
        """
        user, _ = get_user_model().objects.get_or_create(username="admin")
        dataset = create_single_dataset(name="single_dataset", owner=user)
        result = should_be_imported(layer=dataset.name, user=user, skip_existing_layer=True)
        self.assertFalse(result)

    def test_create_alternate_shuould_appen_an_hash(self):
        actual = create_alternate(layer_name="name", execution_id="1234")
        self.assertTrue(actual.startswith("name_"))
        self.assertTrue(len(actual) <= 63)

    def test_create_alternate_shuould_cut_the_hash_if_is_longer_than_63(self):
        actual = create_alternate(
            layer_name="this_is_a_really_long_name_for_a_layer_but_we_need_it_for_test_the_function",
            execution_id="1234",
        )
        self.assertEqual("this_is_a_really_long_name_for_a_layer_but_we_need", actual[:50])
        self.assertTrue(len(actual) <= 63)

    def test_drop_dynamic_model_schema(self):
        _model_schema = ModelSchema(name="model_schema", db_name="datastore", managed=True)
        _model_schema.save()

        self.assertTrue(ModelSchema.objects.filter(name="model_schema").exists())

        # dropping the schema
        drop_dynamic_model_schema(schema_model=_model_schema)

        self.assertFalse(ModelSchema.objects.filter(name="model_schema").exists())

    def test_fixup_name_replace_digits_with_underscore(self):
        """
        Ref https://github.com/GeoNode/geonode/issues/12749
        If the layer start with a digit, we should translate as a string
        """
        layer_name = "1layername"
        expected_name = "_layername"
        actual = BaseHandler().fixup_name(layer_name)
        self.assertEqual(expected_name, actual)
