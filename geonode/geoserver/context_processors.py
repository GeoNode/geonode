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

from django.conf import settings
from django.urls import reverse
from geonode.geoserver.helpers import ogc_server_settings


def geoserver_urls(request):
    """Global values to pass to templates"""
    defaults = dict(
        GEOSERVER_LOCAL_URL=ogc_server_settings.LOCATION,
        GEOSERVER_PUBLIC_LOCATION=ogc_server_settings.public_url,
        GEOSERVER_BASE_URL=ogc_server_settings.public_url,
        UPLOADER_URL=reverse('data_upload'),
        LAYER_ANCILLARY_FILES_UPLOAD_URL=reverse('layer_upload'),
        MAPFISH_PRINT_ENABLED=getattr(ogc_server_settings, 'MAPFISH_PRINT_ENABLED', False),
        PRINT_NG_ENABLED=getattr(ogc_server_settings, 'PRINT_NG_ENABLED', False),
        GEONODE_SECURITY_ENABLED=getattr(ogc_server_settings, 'GEONODE_SECURITY_ENABLED', False),
        TIME_ENABLED=getattr(
            settings,
            'UPLOADER',
            dict()).get(
            'OPTIONS',
            dict()).get(
            'TIME_ENABLED',
            False),
        MOSAIC_ENABLED=getattr(
            settings,
            'UPLOADER',
            dict()).get(
            'OPTIONS',
            dict()).get(
            'MOSAIC_ENABLED',
            False),
    )
    return defaults
