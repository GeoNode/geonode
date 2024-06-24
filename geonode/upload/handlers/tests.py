from django.test import TestCase
from geonode.base.populate_test_data import create_single_dataset
from django.contrib.auth import get_user_model
from dynamic_models.models import ModelSchema
from geonode.upload.handlers.utils import (
    create_alternate,
    drop_dynamic_model_schema,
    should_be_imported,
)


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
