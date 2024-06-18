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

import os
import logging

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from geonode.assets.handlers import asset_handler_registry
from geonode.assets.local import LocalAssetHandler
from geonode.assets.models import Asset, LocalAsset

logger = logging.getLogger(__name__)

TEST_GIF = os.path.join(os.path.dirname(os.path.dirname(__file__)), "base/tests/data/img.gif")


class AssetsTests(APITestCase):

    def test_handler_registry(self):
        # Test registry
        self.assertIsNotNone(asset_handler_registry)
        # Test default handler
        asset_handler = asset_handler_registry.get_default_handler()
        self.assertIsNotNone(asset_handler)
        self.assertIsInstance(asset_handler, LocalAssetHandler, "Bad default Asset handler found")
        # Test None
        self.assertIsNone(asset_handler_registry.get_handler(None))
        # Test class without handler
        self.assertIsNone(asset_handler_registry.get_handler(AssetsTests))

    def test_creation_and_delete_data_cloned(self):
        u, _ = get_user_model().objects.get_or_create(username="admin")
        assets_root = os.path.normpath(settings.ASSETS_ROOT)

        asset_handler = asset_handler_registry.get_default_handler()
        asset = asset_handler.create(
            title="Test Asset",
            description="Description of test asset",
            type="NeverMind",
            owner=u,
            files=[TEST_GIF],
            clone_files=True,
        )
        asset.save()
        self.assertIsInstance(asset, LocalAsset)

        reloaded = Asset.objects.get(pk=asset.pk)
        self.assertIsNotNone(reloaded)
        self.assertIsInstance(reloaded, LocalAsset)
        file = reloaded.location[0]
        self.assertTrue(os.path.exists(file), "Asset file does not exist")
        self.assertTrue(file.startswith(assets_root), f"Asset file is not inside the assets root: {file}")

        cloned_file = file
        reloaded.delete()
        self.assertFalse(Asset.objects.filter(pk=asset.pk).exists())
        self.assertFalse(os.path.exists(cloned_file))
        self.assertFalse(os.path.exists(os.path.dirname(cloned_file)))
        self.assertTrue(os.path.exists(TEST_GIF))

    def test_creation_and_delete_data_external(self):
        u, _ = get_user_model().objects.get_or_create(username="admin")

        asset_handler = asset_handler_registry.get_default_handler()
        asset = asset_handler.create(
            title="Test Asset",
            description="Description of test asset",
            type="NeverMind",
            owner=u,
            files=[TEST_GIF],
            clone_files=False,
        )
        asset.save()
        self.assertIsInstance(asset, LocalAsset)

        reloaded = Asset.objects.get(pk=asset.pk)
        self.assertIsNotNone(reloaded)
        self.assertIsInstance(reloaded, LocalAsset)
        file = reloaded.location[0]
        self.assertEqual(TEST_GIF, file)

        reloaded.delete()
        self.assertFalse(Asset.objects.filter(pk=asset.pk).exists())
        self.assertTrue(os.path.exists(TEST_GIF))

    def test_clone_and_delete_data_managed(self):
        u, _ = get_user_model().objects.get_or_create(username="admin")

        asset_handler = asset_handler_registry.get_default_handler()
        asset = asset_handler.create(
            title="Test Asset",
            description="Description of test asset",
            type="NeverMind",
            owner=u,
            files=[TEST_GIF],
            clone_files=True,
        )
        asset.save()
        self.assertIsInstance(asset, LocalAsset)

        reloaded = Asset.objects.get(pk=asset.pk)
        cloned = asset_handler.clone(reloaded)
        self.assertNotEqual(reloaded.pk, cloned.pk)

        reloaded_file = reloaded.location[0]
        cloned_file = cloned.location[0]

        self.assertNotEqual(reloaded_file, cloned_file)
        self.assertTrue(os.path.exists(reloaded_file))
        self.assertTrue(os.path.exists(cloned_file))

        reloaded.delete()
        self.assertFalse(os.path.exists(reloaded_file))
        self.assertTrue(os.path.exists(cloned_file))

        cloned.delete()
        self.assertFalse(os.path.exists(cloned_file))

    def test_clone_and_delete_data_unmanaged(self):
        u, _ = get_user_model().objects.get_or_create(username="admin")

        asset_handler = asset_handler_registry.get_default_handler()
        asset = asset_handler.create(
            title="Test Asset",
            description="Description of test asset",
            type="NeverMind",
            owner=u,
            files=[TEST_GIF],
            clone_files=False,
        )
        asset.save()
        self.assertIsInstance(asset, LocalAsset)

        reloaded = Asset.objects.get(pk=asset.pk)
        cloned = asset_handler.clone(reloaded)

        self.assertEqual(reloaded.location[0], cloned.location[0])
        self.assertTrue(os.path.exists(reloaded.location[0]))

        reloaded.delete()
        self.assertTrue(os.path.exists(reloaded.location[0]))

        cloned.delete()
        self.assertTrue(os.path.exists(reloaded.location[0]))

    def test_clone_mixed_data(self):
        u, _ = get_user_model().objects.get_or_create(username="admin")

        asset_handler = asset_handler_registry.get_default_handler()
        managed_asset = asset_handler.create(
            title="Test Asset",
            description="Description of test asset",
            type="NeverMind",
            owner=u,
            files=[TEST_GIF],
            clone_files=True,
        )
        managed_asset.save()

        # TODO: dunno if mixed files should be allowed at all
        mixed_asset = asset_handler.create(
            title="Mixed Asset",
            description="Description of test asset",
            type="NeverMind",
            owner=u,
            files=[TEST_GIF, managed_asset.location[0]],
            clone_files=False,  # let's keep both managed and unmanaged together
        )

        reloaded = Asset.objects.get(pk=mixed_asset.pk)

        try:
            asset_handler.clone(reloaded)
            self.fail("A mixed LocalAsset has been cloned")
        except ValueError:
            pass

        mixed_asset.delete()
        managed_asset.delete()
