#########################################################################
#
# Copyright (C) 2021 OSGeo
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

from io import IOBase
from urllib.request import urljoin

from django.urls import reverse
from django.contrib.auth import authenticate

logger = logging.getLogger(__name__)

GEONODE_USER = "admin"
GEONODE_PASSWD = "admin"


def rest_upload_by_path(_file, client, username=GEONODE_USER, password=GEONODE_PASSWD, non_interactive=False):
    """function that uploads a file, or a collection of files, to
    the GeoNode"""
    assert authenticate(username=username, password=password)
    client.login(username=username, password=password)
    spatial_files = ("dbf_file", "shx_file", "prj_file")
    base, ext = os.path.splitext(_file)
    params = {
        # make public since wms client doesn't do authentication
        "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
        "time": "false",
        "charset": "UTF-8",
    }

    # deal with shapefiles
    if ext.lower() == ".shp":
        for spatial_file in spatial_files:
            ext, _ = spatial_file.split("_")
            file_path = f"{base}.{ext}"
            # sometimes a shapefile is missing an extra file,
            # allow for that
            if os.path.exists(file_path):
                params[spatial_file] = open(file_path, "rb")

    with open(_file, "rb") as base_file:
        params["base_file"] = base_file
        for name, value in params.items():
            if isinstance(value, IOBase):
                params[name] = value
        url = urljoin(f"{reverse('uploads-list')}/", "upload/")
        if non_interactive:
            params["non_interactive"] = "true"
        logger.error(f" ---- UPLOAD URL: {url}")
        response = client.post(url, data=params)

    # Closes the files
    for spatial_file in spatial_files:
        if isinstance(params.get(spatial_file), IOBase):
            params[spatial_file].close()

    try:
        logger.error(f" -- response: {response.status_code} / {response.json()}")
        return response, response.json()
    except (ValueError, TypeError):
        logger.exception(ValueError(f"probably not json, status {response.status_code} / {response.content}"))
        return response, response.content
