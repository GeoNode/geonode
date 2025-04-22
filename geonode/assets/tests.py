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
import shutil
import io
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import StreamingHttpResponse
from django.urls import reverse

from rest_framework.test import APITestCase

from geonode.assets.handlers import asset_handler_registry
from geonode.assets.local import LocalAssetHandler
from geonode.assets.models import Asset, LocalAsset

logger = logging.getLogger(__name__)

ONE_JSON = os.path.join(os.path.dirname(__file__), "tests/data/one.json")
TWO_JSON = os.path.join(os.path.dirname(__file__), "tests/data/two.json")
THREE_JSON = os.path.join(os.path.dirname(__file__), "tests/data/three.json")


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
            files=[ONE_JSON],
            clone_files=True,
        )
        asset.save()
        self.assertIsInstance(asset, LocalAsset)

        reloaded = LocalAsset.objects.get(pk=asset.pk)
        self.assertIsNotNone(reloaded)
        self.assertIsInstance(reloaded, LocalAsset)
        file = reloaded.location[0]
        self.assertTrue(os.path.exists(file), "Asset file does not exist")
        self.assertTrue(
            os.path.normpath(file).startswith(os.path.normpath(assets_root)),
            f"Asset file is not inside the assets root: {file}",
        )

        cloned_file = file
        reloaded.delete()
        self.assertFalse(Asset.objects.filter(pk=asset.pk).exists())
        self.assertFalse(os.path.exists(cloned_file))
        self.assertFalse(os.path.exists(os.path.dirname(cloned_file)))
        self.assertTrue(os.path.exists(ONE_JSON))

    def test_creation_and_delete_data_external(self):
        u, _ = get_user_model().objects.get_or_create(username="admin")

        asset_handler = asset_handler_registry.get_default_handler()
        asset = asset_handler.create(
            title="Test Asset",
            description="Description of test asset",
            type="NeverMind",
            owner=u,
            files=[ONE_JSON],
            clone_files=False,
        )
        asset.save()
        self.assertIsInstance(asset, LocalAsset)

        reloaded = LocalAsset.objects.get(pk=asset.pk)
        self.assertIsNotNone(reloaded)
        self.assertIsInstance(reloaded, LocalAsset)
        file = reloaded.location[0]
        self.assertEqual(ONE_JSON, file)

        reloaded.delete()
        self.assertFalse(Asset.objects.filter(pk=asset.pk).exists())
        self.assertTrue(os.path.exists(ONE_JSON))

    def test_clone_and_delete_data_managed(self):
        u, _ = get_user_model().objects.get_or_create(username="admin")

        asset_handler = asset_handler_registry.get_default_handler()
        asset = asset_handler.create(
            title="Test Asset",
            description="Description of test asset",
            type="NeverMind",
            owner=u,
            files=[ONE_JSON],
            clone_files=True,
        )
        asset.save()
        self.assertIsInstance(asset, LocalAsset)

        reloaded = LocalAsset.objects.get(pk=asset.pk)
        cloned = asset_handler.clone(reloaded)
        self.assertNotEqual(reloaded.pk, cloned.pk)

        reloaded_file = os.path.normpath(reloaded.location[0])
        cloned_file = os.path.normpath(cloned.location[0])

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
            files=[ONE_JSON],
            clone_files=False,
        )
        asset.save()
        self.assertIsInstance(asset, LocalAsset)

        reloaded = LocalAsset.objects.get(pk=asset.pk)
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
            files=[ONE_JSON],
            clone_files=True,
        )
        managed_asset.save()

        # TODO: dunno if mixed files should be allowed at all
        mixed_asset = asset_handler.create(
            title="Mixed Asset",
            description="Description of test asset",
            type="NeverMind",
            owner=u,
            files=[THREE_JSON, managed_asset.location[0]],
            clone_files=False,  # let's keep both managed and unmanaged together
        )

        reloaded = Asset.objects.get(pk=mixed_asset.pk)

        try:
            asset_handler.clone(reloaded)
            self.fail("A mixed LocalAsset has been cloned")
        except ValueError:
            pass

        managed_asset.delete()

        try:
            mixed_asset.delete()
            self.fail("Missed mixed LocalAsset detection")
        except ValueError:
            pass


class AssetsDownloadTests(APITestCase):

    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    def _get_streaming_content(self, response):
        with io.BytesIO(b"".join(response.streaming_content)) as buf_bytes:
            return buf_bytes.read()

    def test_download_file(self):
        u, _ = get_user_model().objects.get_or_create(username="admin")
        self.assertTrue(self.client.login(username="admin", password="admin"), "Login failed")

        asset = self._setup_test(u)

        for path, key in ((None, "one"), ("one.json", "one"), ("two.json", "two"), ("subdir/three.json", "three")):
            # args = [asset.pk, path] if path else [asset.pk]
            args = {"pk": asset.pk, "path": path} if path else {"pk": asset.pk}
            logger.info(f"*** Testing path '{path}' args {args}")
            url = reverse("assets-link", kwargs=args)
            logger.info(f"REVERSE url is {url}")
            response = self.client.get(url)
            content = self._get_streaming_content(response)
            rjson = json.loads(content)
            self.assertEqual(response.status_code, 200)
            self.assertIn(key, rjson, f"Key '{key}' not found in path '{path}': {rjson} URL {url}")
            logger.info(f"Test for path '{path}' OK")

    def test_download_with_attachment(self):
        u, _ = get_user_model().objects.get_or_create(username="admin")
        self.assertTrue(self.client.login(username="admin", password="admin"), "Login failed")

        for key, el in (("one", ONE_JSON), ("two", TWO_JSON), ("three", THREE_JSON)):
            asset = self._setup_test(u, _file=el)

            url = reverse("assets-download", kwargs={"pk": asset.pk})
            logger.info(f"REVERSE url is {url}")
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(isinstance(response, StreamingHttpResponse))
            self.assertEqual(response.get("Content-Disposition"), f"attachment; filename={key}.zip")

    def test_download_with_attachment_with_no_download_perms(self):
        """
        any user without download permissions
        cannot download the asset
        """
        from geonode.resource.manager import resource_manager
        from geonode.layers.models import Dataset
        from guardian.shortcuts import get_anonymous_user

        bobby, _ = get_user_model().objects.get_or_create(username="bobby")

        self.client.force_login(get_user_model().objects.get(username="norman"))
        for _, el in (("one", ONE_JSON), ("two", TWO_JSON), ("three", THREE_JSON)):
            asset = self._setup_test(bobby, _file=el)
            resource = None
            try:
                # creating resoruce
                resource = resource_manager.create(
                    None, resource_type=Dataset, defaults={"owner": bobby, "asset": asset}
                )
                # getting perms
                # remove perms for user bobby
                resource_perms = resource.get_all_level_info()
                resource_perms["users"][bobby] = ["view_resourcebase"]
                # and anonymous just to be sure
                resource_perms["groups"][get_anonymous_user().groups.first()] = ["view_resourcebase"]
                # resetting the permissions for the resource
                resource_manager.set_permissions(resource.uuid, instance=resource, permissions=resource_perms)
                url = reverse("assets-download", kwargs={"pk": asset.pk})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)
            except Exception as e:
                logger.exception(e)
            finally:
                if resource:
                    resource.delete()

    def _setup_test(self, u, _file=ONE_JSON):
        asset_handler = asset_handler_registry.get_default_handler()
        asset = asset_handler.create(
            title="Test Asset",
            description="Description of test asset",
            type="NeverMind",
            owner=u,
            files=[_file],
            clone_files=True,
        )
        asset.save()
        self.assertIsInstance(asset, LocalAsset)

        reloaded = LocalAsset.objects.get(pk=asset.pk)

        # put two more files in the asset dir
        asset_dir = os.path.dirname(reloaded.location[0])
        sub_dir = os.path.join(asset_dir, "subdir")
        os.mkdir(sub_dir)
        shutil.copy(TWO_JSON, asset_dir)
        shutil.copy(THREE_JSON, sub_dir)
        return asset
