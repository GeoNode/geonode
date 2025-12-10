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
from types import SimpleNamespace

from unittest.mock import patch

from django.test import override_settings

from geonode.base.i18n import i18nCache
from geonode.base.models import ResourceBase
from geonode.metadata.handlers.multilang import MultiLangHandler
from geonode.metadata.handlers.sparse import SparseHandler, SparseFieldRegistry
from geonode.metadata.manager import MetadataManager
from geonode.metadata.tests.handlers import FakeHandler, LoaderHandler

from geonode.tests.base import GeoNodeBaseTestSupport


logger = logging.getLogger(__name__)


class IndexingInvocationTests(GeoNodeBaseTestSupport):

    def setUp(self):
        i18nCache.clear()

    def tearDown(self):
        super().tearDown()

    def create_metadata_manager(self):
        sr = SparseFieldRegistry()
        mm = MetadataManager()
        mm.handlers = {
            # "base": BaseHandler(),
            "loader": LoaderHandler(schemafile=os.path.join(os.path.dirname(__file__), "data/minimal_schema.json")),
            "fake": FakeHandler(),
            "sparse": SparseHandler(registry=sr),
            "multilang": MultiLangHandler(registry=sr),
        }
        mm.post_init()
        return mm, sr

    @patch("geonode.base.models.ResourceBase.get_real_instance_class")
    @patch("geonode.indexing.manager.TSVectorIndexManager.update_index")
    @patch("geonode.metadata.handlers.sparse.SparseHandler.update_resource")
    def test_indexmanager_invocation(self, mock_get_real_instance_class, mock_update_index, mock_sparse_update):
        """
        The index manager should be called when the metadata are saved
        """
        with override_settings(
            LANGUAGE_CODE="it",
            LANGUAGES=[("en", "English"), ("it", "Italiano")],
            MULTILANG_FIELDS=["title"],
        ):
            mm, _ = self.create_metadata_manager()
            self.assertNotIn("base", mm.handlers)
            instance = {
                "title": "whatever",
                "title_multilang_it": "title_it",
                "title_multilang_en": None,
                "abstract": "abstract_fake",
                "license": "license_fake",
            }

            resource = ResourceBase()
            fake_req = SimpleNamespace(data=instance, user=None)
            mm.update_schema_instance(resource, fake_req)

            mock_update_index.assert_called_once()
