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

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import json

from rest_framework import status

from actstream import registry
from actstream.models import Action

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.layers.populate_datasets_data import create_dataset_data
from geonode.social.templatetags.social_tags import activity_item
from geonode.layers.models import Dataset
from geonode.base.populate_test_data import all_public, create_models, remove_models


class RecentActivityTest(GeoNodeBaseTestSupport):
    integration = True

    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

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
        super(RecentActivityTest, self).setUp()

        registry.register(Dataset)
        registry.register(get_user_model())
        create_dataset_data()
        self.user = get_user_model().objects.filter(username="admin")[0]

    def test_dataset_activity(self):
        """
        Tests the activity functionality when a layer is saved.
        """

        # A new activity should be created for each Dataset.
        self.assertNotEqual(Action.objects.all().count(), Dataset.objects.all().count())

        action = Action.objects.first()
        dataset = action.action_object

        # The activity should read:
        # layer.owner (actor) 'uploaded' (verb) layer (object)
        self.assertEqual(action.actor, action.action_object.owner)
        data = action.data
        if isinstance(data, (str, bytes)):
            data = json.loads(data)
        self.assertEqual(data.get("raw_action"), "created")
        self.assertEqual(data.get("object_name"), dataset.name)
        self.assertTrue(isinstance(action.action_object, Dataset))
        self.assertIsNone(action.target)

        # Test the  activity_item template tag
        template_tag = activity_item(Action.objects.first())

        self.assertEqual(template_tag.get("username"), action.actor.username)
        self.assertEqual(template_tag.get("object_name"), dataset.name)
        self.assertEqual(template_tag.get("actor"), action.actor)
        self.assertEqual(template_tag.get("verb"), _("uploaded"))
        self.assertEqual(template_tag.get("action"), action)
        self.assertEqual(template_tag.get("activity_class"), "upload")

        dataset_name = dataset.name
        dataset.delete()

        # <user> deleted <object_name>
        action = Action.objects.first()
        data = action.data
        if isinstance(data, (str, bytes)):
            data = json.loads(data)
        self.assertEqual(data.get("raw_action"), "deleted")
        self.assertEqual(data.get("object_name"), dataset_name)

        # objects are literally deleted so no action object or target should be related to a delete action.
        self.assertIsNone(action.action_object)
        self.assertIsNone(action.target)

        # Test the activity_item template tag
        action = Action.objects.first()
        template_tag = activity_item(action)

        # Make sure the 'delete' class is returned
        self.assertEqual(template_tag.get("activity_class"), "delete")

        # The layer's name should be returned
        self.assertEqual(template_tag.get("object_name"), dataset_name)
        self.assertEqual(template_tag.get("verb"), _("deleted"))

    def test_get_recent_activities(self):
        url = reverse("recent-activity")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.context_data["action_list_geoapps"])
        self.assertIsNotNone(response.context_data["action_list_datasets"])
        self.assertIsNotNone(response.context_data["action_list_maps"])
        self.assertIsNotNone(response.context_data["action_list_documents"])
