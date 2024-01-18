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
import xml.etree.ElementTree as ET

from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.template.loader import get_template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from geonode.base.auth import get_or_create_token
from geonode.geoserver.helpers import wps_format_is_supported
from geonode.layers.views import _resolve_dataset
from geonode.proxy.views import fetch_response_headers
from geonode.utils import HttpClient

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
        resource = self.get_resource()
        if not resource:
            raise Http404("Resource requested is not available")
        response = self.process_dowload(resource)
        return response

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
        if resource.subtype not in ["vector", "raster", "vector_time"]:
            logger.info("Download URL is available only for datasets that have been harvested and copied locally")
            return None

        if self.is_link_resource:
            return resource.link_set.filter(resource=resource.get_self_resource(), link_type="original").first().url

        return reverse("dataset_download", args=[resource.alternate])

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

    def process_dowload(self, resource=None):
        """
        Generate the response object
        """
        if not resource:
            resource = self.get_resource()
        if not settings.USE_GEOSERVER:
            # if GeoServer is not used, we redirect to the proxy download
            return HttpResponseRedirect(reverse("download", args=[resource.id]))

        download_format = self.request.GET.get("export_format")

        if download_format and not wps_format_is_supported(download_format, resource.subtype):
            logger.error("The format provided is not valid for the selected resource")
            return JsonResponse({"error": "The format provided is not valid for the selected resource"}, status=500)

        _format = "application/zip" if resource.is_vector() else "image/tiff"
        # getting default payload
        tpl = get_template("geoserver/dataset_download.xml")
        ctx = {"alternate": resource.alternate, "download_format": download_format or _format}
        # applying context for the payload
        payload = tpl.render(ctx)

        # init of Client
        client = HttpClient()

        headers = {"Content-type": "application/xml", "Accept": "application/xml"}

        # defining the URL needed fr the download
        url = f"{settings.OGC_SERVER['default']['LOCATION']}ows?service=WPS&version=1.0.0&REQUEST=Execute"
        if not self.request.user.is_anonymous:
            # define access token for the user
            access_token = get_or_create_token(self.request.user)
            url += f"&access_token={access_token}"

        # request to geoserver
        response, content = client.request(url=url, data=payload, method="post", headers=headers)

        if not response or response.status_code != 200:
            logger.error(f"Download dataset exception: error during call with GeoServer: {content}")
            return JsonResponse(
                {"error": "Download dataset exception: error during call with GeoServer"},
                status=500,
            )

        # error handling
        namespaces = {"ows": "http://www.opengis.net/ows/1.1", "wps": "http://www.opengis.net/wps/1.0.0"}
        response_type = response.headers.get("Content-Type")
        if response_type == "text/xml":
            # parsing XML for get exception
            content = ET.fromstring(response.text)
            exc = content.find("*//ows:Exception", namespaces=namespaces) or content.find(
                "ows:Exception", namespaces=namespaces
            )
            if exc:
                exc_text = exc.find("ows:ExceptionText", namespaces=namespaces)
                logger.error(f"{exc.attrib.get('exceptionCode')} {exc_text.text}")
                return JsonResponse({"error": f"{exc.attrib.get('exceptionCode')}: {exc_text.text}"}, status=500)

        return_response = fetch_response_headers(
            HttpResponse(content=response.content, status=response.status_code, content_type=download_format),
            response.headers,
        )
        return_response.headers["Content-Type"] = download_format or _format
        return return_response
