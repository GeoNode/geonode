#########################################################################
#
# Copyright (C) 2016 OSGeo
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

from geonode.base.models import ResourceBase
from geonode.tests.base import GeoNodeBaseTestSupport

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from .models import Favorite
from geonode.documents.models import Document
from geonode.base.populate_test_data import all_public, create_models, remove_models, create_single_dataset


class FavoriteTest(GeoNodeBaseTestSupport):
    type = "document"

    """
    Tests geonode.favorite app/module
    """

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
        self.adm_un = "admin"
        self.adm_pw = "admin"

    # tests of Favorite and FavoriteManager methods.
    def test_favorite(self):
        # assume we created at least one User and two Documents in setUp.
        test_user = get_user_model().objects.first()
        test_document_1 = Document.objects.first()
        test_document_2 = Document.objects.last()
        self.assertIsNotNone(test_document_1)
        self.assertIsNotNone(test_document_2)

        # test create favorite.
        Favorite.objects.create_favorite(test_document_1, test_user)
        Favorite.objects.create_favorite(test_document_2, test_user)
        favorites = Favorite.objects.all()
        self.assertEqual(favorites.count(), 2)
        ct = ContentType.objects.get_for_model(test_document_1)
        self.assertEqual(favorites[0].content_type, ct)

        # test all favorites for specific user.
        favorites_for_user = Favorite.objects.favorites_for_user(test_user)
        self.assertEqual(favorites_for_user.count(), 2)

        # test document favorites for user.
        document_favorites = Favorite.objects.favorite_documents_for_user(test_user)
        self.assertEqual(document_favorites.count(), 2)

        # test layer favorites for user.
        dataset_favorites = Favorite.objects.favorite_datasets_for_user(test_user)
        self.assertEqual(dataset_favorites.count(), 0)

        # test map favorites for user.
        map_favorites = Favorite.objects.favorite_maps_for_user(test_user)
        self.assertEqual(map_favorites.count(), 0)

        # test user favorites for user.
        user_favorites = Favorite.objects.favorite_users_for_user(test_user)
        self.assertEqual(user_favorites.count(), 0)

        # test favorite for user and a specific content object.
        user_content_favorite = Favorite.objects.favorite_for_user_and_content_object(test_user, test_document_1)
        self.assertEqual(user_content_favorite.object_id, test_document_1.id)

        # test bulk favorites.
        bulk_favorites = Favorite.objects.bulk_favorite_objects(test_user)
        self.assertEqual(len(bulk_favorites[ct.name]), 2)
        self.assertEqual(len(bulk_favorites["user"]), 0)

    def test_given_resource_base_object_will_assign_subtype_as_content_type(self):
        test_user = get_user_model().objects.first()

        """
        If the input object is a ResourceBase, in favorite content type, should be saved he
        subtype content type (Doc, Dataset, Map or GeoApp)
        """
        create_single_dataset("foo_dataset")
        resource = ResourceBase.objects.get(title="foo_dataset")
        created_fav = Favorite.objects.create_favorite(resource, test_user)
        self.assertEqual("dataset", created_fav.content_type.model)

        """
        If the input object is a subtype, should save the relative content type
        """
        test_document_1 = Document.objects.first()
        self.assertIsNotNone(test_document_1)
        Favorite.objects.create_favorite(test_document_1, test_user)
        fav = Favorite.objects.last()
        ct = ContentType.objects.get_for_model(test_document_1)
        self.assertEqual(fav.content_type, ct)

    def _get_response(self, input_url, input_args):
        return self.client.post(reverse(input_url, args=input_args), content_type="application/json")
