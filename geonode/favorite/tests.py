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

import json
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.db.models import Max

from .models import Favorite
from geonode.geoapps.models import GeoApp
from geonode.documents.models import Document
from geonode.base.populate_test_data import (
    all_public,
    create_models,
    remove_models,
    create_single_layer)


class FavoriteTest(GeoNodeBaseTestSupport):

    type = 'document'

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
        self.admin = get_user_model().objects.get(username="admin")
        self.geoapp = GeoApp.objects.create(
            uuid=str(uuid4()),
            resource_type='geoapp',
            name="test geoapp1",
            owner=self.admin)

    # tests of Favorite and FavoriteManager methods.
    def test_favorite(self):
        # assume we created at least one User and two Documents in setUp.
        test_user = get_user_model().objects.first()
        test_user2 = get_user_model().objects.last()
        test_document_1 = Document.objects.first()
        test_document_2 = Document.objects.last()
        test_geoapp_1 = GeoApp.objects.first()
        self.assertIsNotNone(test_document_1)
        self.assertIsNotNone(test_document_2)
        self.assertIsNotNone(test_geoapp_1)

        # test create favorite.
        Favorite.objects.create_favorite(test_document_1, test_user)
        Favorite.objects.create_favorite(test_document_2, test_user)
        Favorite.objects.create_favorite(test_geoapp_1, test_user2)

        favorites = Favorite.objects.all()
        self.assertEqual(favorites.count(), 3)
        ct = ContentType.objects.get_for_model(test_document_1)
        self.assertEqual(favorites[0].content_type, ct)

        # test all favorites for specific user.
        favorites_for_user = Favorite.objects.favorites_for_user(test_user)
        self.assertEqual(favorites_for_user.count(), 2)

        # test document favorites for user.
        document_favorites = Favorite.objects.favorite_documents_for_user(test_user)
        self.assertEqual(document_favorites.count(), 2)

        # test layer favorites for user.
        layer_favorites = Favorite.objects.favorite_layers_for_user(test_user)
        self.assertEqual(layer_favorites.count(), 0)

        # test map favorites for user.
        map_favorites = Favorite.objects.favorite_maps_for_user(test_user)
        self.assertEqual(map_favorites.count(), 0)

        # test user favorites for user.
        user_favorites = Favorite.objects.favorite_users_for_user(test_user)
        self.assertEqual(user_favorites.count(), 0)

        # test favorite for user and a specific content object.
        user_content_favorite = Favorite.objects.favorite_for_user_and_content_object(test_user, test_document_1)
        self.assertEqual(user_content_favorite.object_id, test_document_1.id)

        # test favorite for user and a specific content object for geoapp.
        user_content_favorite = Favorite.objects.favorite_for_user_and_content_object(test_user2, test_geoapp_1)
        self.assertEqual(user_content_favorite.object_id, test_geoapp_1.id)

        # test bulk favorites.
        bulk_favorites = Favorite.objects.bulk_favorite_objects(test_user)
        self.assertEqual(len(bulk_favorites[ct.name]), 2)
        self.assertEqual(len(bulk_favorites["user"]), 0)

    def test_given_resource_base_object_will_assign_subtype_as_content_type(self):
        test_user = get_user_model().objects.first()

        '''
        If the input object is a ResourceBase, in favorite content type, should be saved he
        subtype content type (Doc, Layer, Map or GeoApp)
        '''
        create_single_layer('foo_layer')
        resource = ResourceBase.objects.get(title='foo_layer')
        created_fav = Favorite.objects.create_favorite(resource, test_user)
        self.assertEqual('layer', created_fav.content_type.model)

        '''
        If the input object is a subtype, should save the relative content type
        '''
        test_document_1 = Document.objects.first()
        self.assertIsNotNone(test_document_1)
        Favorite.objects.create_favorite(test_document_1, test_user)
        fav = Favorite.objects.last()
        ct = ContentType.objects.get_for_model(test_document_1)
        self.assertEqual(fav.content_type, ct)

    # tests of view methods.
    def test_create_favorite_view(self):
        """
        call create view with valid user and content.
        then call again to check for idempotent.
        """
        self.client.login(username=self.adm_un, password=self.adm_pw)

        document = Document.objects.first()
        self.assertIsNotNone(document)
        document_pk = document.pk
        response = self._get_response("add_favorite_document", (document_pk,))

        # check persisted.
        self.assertEqual(Favorite.objects.count(), 1)
        ct = ContentType.objects.get_for_model(Document)
        self.assertEqual(Favorite.objects.first().content_type, ct)
        favorite_pk = Favorite.objects.first().pk

        # check response.
        self.assertEqual(response.status_code, 200)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        json_content = json.loads(content)
        self.assertEqual(json_content["has_favorite"], "true")
        expected_delete_url = reverse("delete_favorite", args=[favorite_pk])
        self.assertEqual(json_content["delete_url"], expected_delete_url)

        # call method again, check for idempotent.
        document = Document.objects.first()
        self.assertIsNotNone(document)
        document_pk = document.pk
        response2 = self._get_response("add_favorite_document", (document_pk,))

        # check still one only persisted, same as before second call.
        self.assertEqual(Favorite.objects.count(), 1)
        self.assertEqual(Favorite.objects.first().content_type, ct)

        # check second response.
        self.assertEqual(response2.status_code, 200)
        json_content2 = json.loads(response2.content)
        self.assertEqual(json_content2["has_favorite"], "true")
        self.assertEqual(json_content2["delete_url"], expected_delete_url)

        # test favourite geoapp from view
        response = self._get_response("add_favorite_geoapp", (self.geoapp.pk,))
        self.assertEqual(response.status_code, 200)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        json_content = json.loads(content)
        self.assertEqual(json_content["has_favorite"], "true")
        expected_delete_url = reverse("delete_favorite", args=[self.geoapp.pk])

    def test_create_favorite_view_login_required(self):
        """
        call create view, not logged in.
        expect a redirect to login page.
        """
        response = self._get_response("add_favorite_document", ("1",))
        self.assertEqual(response.status_code, 302)

    def test_create_favorite_view_id_not_found(self):
        """
        call create view with object id that does not exist.
        expect not found.
        """
        # get a pk that is not in the db for Document object.
        max_document_pk = Document.objects.aggregate(Max("pk"))
        self.assertIsNotNone(max_document_pk)
        pk_not_in_db = str(max_document_pk["pk__max"] + 1)

        self.client.login(username=self.adm_un, password=self.adm_pw)
        response = self._get_response("add_favorite_document", (pk_not_in_db,))
        self.assertEqual(response.status_code, 404)

    def test_delete_favorite_view(self):
        """
        call delete view with valid user and favorite id.
        then call again to check for idempotent.
        """
        self.client.login(username=self.adm_un, password=self.adm_pw)

        # first, add one to delete.
        document = Document.objects.first()
        self.assertIsNotNone(document)
        document_pk = document.pk
        response = self._get_response("add_favorite_document", (document_pk,))

        # check persisted.
        self.assertEqual(Favorite.objects.count(), 1)
        ct = ContentType.objects.get_for_model(Document)
        self.assertEqual(Favorite.objects.first().content_type, ct)
        favorite_pk = Favorite.objects.first().pk

        # call delete method.
        response = self._get_response("delete_favorite", (favorite_pk,))

        # check no longer persisted.
        self.assertEqual(Favorite.objects.count(), 0)

        # check response.
        self.assertEqual(response.status_code, 200)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        json_content = json.loads(content)
        self.assertEqual(json_content["has_favorite"], "false")

        # call method again, check for idempotent.
        response2 = self._get_response("delete_favorite", (favorite_pk,))

        # check still none persisted, same as before second call.
        self.assertEqual(Favorite.objects.count(), 0)

        # check second response.
        self.assertEqual(response2.status_code, 200)
        json_content2 = json.loads(response2.content)
        self.assertEqual(json_content2["has_favorite"], "false")

        # test delete geoapp from favorite
        response = self._get_response("delete_favorite", (self.geoapp.pk,))
        self.assertEqual(response.status_code, 200)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        json_content = json.loads(content)
        self.assertEqual(json_content["has_favorite"], "false")

    def test_delete_favorite_view_login_required(self):
        """
        call delete view, not logged in.
        expect a redirect to login page.
        """
        response = self._get_response("delete_favorite", ("1",))
        self.assertEqual(response.status_code, 302)

    def _get_response(self, input_url, input_args):
        return self.client.post(
            reverse(
                input_url,
                args=input_args
            ),
            content_type="application/json"
        )
