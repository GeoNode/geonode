#########################################################################
#
# Copyright (C) 2023 OSGeo
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

import logging

from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from geonode.layers.views import _resolve_dataset

logger = logging.getLogger("geonode.layers.download_handler")


class DatasetDownloadHandler:
    def __str__(self):
        return f"{self.__module__}.{self.__class__.__name__}"

    def __repr__(self):
        return self.__str__()

    def __init__(self, request, resource_name) -> None:
        self.request = request
        self.resource_name = resource_name
        self._resource = None

    def get_download_response(self):
        """
        Basic method. Should return the Response object
        that allow the resource download
        """
        raise Http404("Direct download for the requested resource is not supported")

    @property
    def is_link_resource(self):
        resource = self.get_resource()
        return resource.link_set.filter(resource=resource, link_type="original").exists()

    @property
    def is_ajax_safe(self):
        """
        AJAX is safe to be used for WPS downloads. In case of a link set in a Link entry we cannot assume it,
        since it could point to an external (non CORS enabled) URL
        """
        return settings.USE_GEOSERVER and not self.is_link_resource

    @property
    def download_url(self):
        resource = self.get_resource()
        if not resource:
            return None
        if not resource.can_be_downloaded:
            logger.info("Download URL is available only for datasets that have been harvested and copied locally")
            return None

        if self.is_link_resource:
            return resource.link_set.filter(resource=resource.get_self_resource(), link_type="original").first().url

        return None

    def get_resource(self):
        """
        Returnt the object needed
        """
        if not self._resource:
            try:
                self._resource = _resolve_dataset(
                    self.request,
                    self.resource_name,
                    "base.download_resourcebase",
                    _("You do not have download permissions for this dataset."),
                )
            except Exception as e:
                logger.debug(e)

        return self._resource

