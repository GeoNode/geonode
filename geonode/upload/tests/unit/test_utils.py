#########################################################################
#
# Copyright (C) 2018 OSGeo
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

"""unit tests for geonode.upload.utils module"""

from django.conf import settings

from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.upload.models import UploadSizeLimit, UploadParallelismLimit
from geonode.upload.utils import get_max_upload_size, get_max_upload_parallelism_limit


class UtilsTestCase(GeoNodeBaseTestSupport):

    def test_get_max_upload_size(self):
        upload_size = UploadSizeLimit.objects.create(slug="test_slug", max_size=1000, description="test description")
        # get upload size of existing obj
        self.assertEqual(get_max_upload_size("test_slug"), 1000)

        # get upload size of non existing obj will return settings default max size
        self.assertEqual(get_max_upload_size("invalid"), getattr(settings, "DEFAULT_MAX_UPLOAD_SIZE", 104857600))
        upload_size.delete()

    def test_get_max_upload_parallelism_limit(self):
        upload_parallelism_limit = UploadParallelismLimit.objects.create(
            slug="test_slug", max_number=3, description="test description"
        )
        # get upload parallelism limit of existing obj
        self.assertEqual(get_max_upload_parallelism_limit("test_slug"), 3)

        # get upload parallelism limit of non existing obj will return settings default max size
        self.assertEqual(
            get_max_upload_parallelism_limit("invalid"), getattr(settings, "DEFAULT_MAX_PARALLEL_UPLOADS_PER_USER", 5)
        )
        # cleanUp
        upload_parallelism_limit.delete()
