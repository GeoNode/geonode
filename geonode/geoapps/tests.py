#########################################################################
#
# Copyright (C) 2020 OSGeo
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

from django.urls import reverse
from django.contrib.auth import get_user_model

from geonode.geoapps.models import GeoApp
from geonode.base.models import TopicCategory, Region, Thesaurus, ThesaurusKeyword
from geonode.groups.models import GroupProfile
from geonode.resource.registry import resource_manager_registry, geoapp_manager
from geonode.security.registry import permissions_registry
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.metadata.manager import metadata_manager
from geonode.base.populate_test_data import all_public, create_models, remove_models


class GeoAppTests(GeoNodeBaseTestSupport):
    """Tests geonode.geoapps module"""

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
        super().setUp()
        self.bobby = get_user_model().objects.get(username="bobby")
        self.geo_app = geoapp_manager.create(
            None,
            resource_type=GeoApp,
            defaults=dict(
                title="Testing GeoApp", owner=self.bobby, blob='{"test_data": {"test": ["test_1","test_2","test_3"]}}'
            ),
        )
        self.user = get_user_model().objects.get(username="admin")
        self.geoapp = GeoApp.objects.create(
            name="name", title="geoapp_titlte", thumbnail_url="initial", owner=self.user
        )

    def test_geoapp_category_is_correctly_assigned_in_metadata_upload(self):
        self.client.login(username="admin", password="admin")
        url = reverse("metadata-schema_instance", args=(self.geoapp.id,))

        # assign a category to the GeoApp
        category = TopicCategory.objects.order_by("identifier").first()
        self.geoapp.category = category
        self.geoapp.save()
        # retrieving the new one
        new_category = TopicCategory.objects.order_by("identifier").last()

        payload = metadata_manager.build_schema_instance(self.geoapp)
        payload["category"] = {"id": new_category.identifier}
        response = self.client.put(url, data=payload, content_type="application/json")

        self.geoapp.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(new_category.identifier, self.geoapp.category.identifier)

    def test_geoapp_copy(self):
        self.client.login(username="admin", password="admin")
        geoapp_copy = None
        try:
            geoapp_copy = resource_manager_registry.get_for_instance(self.geoapp).copy(
                self.geoapp, defaults=dict(title="Testing GeoApp 2")
            )
            self.assertIsNotNone(geoapp_copy)
            self.assertEqual(geoapp_copy.title, "Testing GeoApp 2")
        finally:
            if geoapp_copy:
                geoapp_copy.delete()
            self.assertIsNotNone(self.geoapp)

    def test_geoapp_copy_carries_over_metadata_and_permissions(self):
        """Same fix as the Dataset/Map copy (cloning fix): M2M metadata and the source's own
        perm_spec must survive a GeoApp copy too, the copy() logic in BaseResourceManager is generic."""
        self.client.login(username="admin", password="admin")
        # geoapp_manager.update() only forwards `vals` to GeoApp's own _create_and_update(),
        # keywords/regions kwargs would be silently dropped, so set M2M fields directly instead
        region = Region.objects.first()
        self.geoapp = geoapp_manager.update(
            self.geoapp.uuid, instance=self.geoapp, vals={"abstract": "test abstract", "purpose": "test purpose"}
        )
        self.geoapp.keywords.add("foo", "bar")
        self.geoapp.regions.add(region)
        thesaurus = Thesaurus.objects.create(identifier="test_thesaurus_geoapp_copy", title="Test Thesaurus")
        tkeyword = ThesaurusKeyword.objects.create(thesaurus=thesaurus, alt_label="test_tkeyword")
        self.geoapp.tkeywords.add(tkeyword)

        custom_group, _ = GroupProfile.objects.get_or_create(
            slug="geoapp_copy_group", title="geoapp_copy_group", access="private"
        )
        custom_perms = {
            "users": {self.bobby.username: ["view_resourcebase", "change_resourcebase"]},
            "groups": {custom_group.slug: ["view_resourcebase"]},
        }
        geoapp_manager.set_permissions(self.geoapp.uuid, instance=self.geoapp, permissions=custom_perms)

        geoapp_copy = None
        try:
            geoapp_copy = resource_manager_registry.get_for_instance(self.geoapp).copy(
                self.geoapp, defaults=dict(title="Testing GeoApp Metadata Copy")
            )
            self.assertIsNotNone(geoapp_copy)
            self.assertEqual(self.geoapp.abstract, geoapp_copy.abstract)
            self.assertEqual(self.geoapp.purpose, geoapp_copy.purpose)
            self.assertCountEqual(
                [k.name for k in self.geoapp.keywords.all()], [k.name for k in geoapp_copy.keywords.all()]
            )
            self.assertCountEqual(list(self.geoapp.regions.all()), list(geoapp_copy.regions.all()))
            self.assertCountEqual(list(self.geoapp.tkeywords.all()), list(geoapp_copy.tkeywords.all()))

            source_perms = permissions_registry.get_perms(instance=self.geoapp, include_virtual=False)
            copy_perms = permissions_registry.get_perms(instance=geoapp_copy, include_virtual=False)
            for perm_key in ("users", "groups"):
                source_entries = {profile.pk: set(perms) for profile, perms in source_perms.get(perm_key, {}).items()}
                copy_entries = {profile.pk: set(perms) for profile, perms in copy_perms.get(perm_key, {}).items()}
                self.assertEqual(source_entries, copy_entries)
        finally:
            if geoapp_copy:
                geoapp_copy.delete()
            self.assertIsNotNone(self.geoapp)
