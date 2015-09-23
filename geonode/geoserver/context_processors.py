#########################################################################
#
# Copyright (C) 2012 OpenPlans
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
from django.core.urlresolvers import reverse
from geonode.geoserver.helpers import ogc_server_settings


def geoserver_urls(request):
    """Global values to pass to templates"""
    defaults = dict(
        GEOSERVER_BASE_URL=ogc_server_settings.public_url,
        UPLOADER_URL=reverse('data_upload') if getattr(
            settings,
            'UPLOADER',
            dict()).get(
            'BACKEND',
            'geonode.rest') == 'geonode.importer' else reverse('layer_upload'),
        MAPFISH_PRINT_ENABLED=ogc_server_settings.MAPFISH_PRINT_ENABLED,
        PRINT_NG_ENABLED=ogc_server_settings.PRINT_NG_ENABLED,
        GEONODE_SECURITY_ENABLED=ogc_server_settings.GEONODE_SECURITY_ENABLED,
        GEOGIG_ENABLED=ogc_server_settings.GEOGIG_ENABLED,
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
