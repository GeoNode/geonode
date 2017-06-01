# -*- coding: utf-8 -*-
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
from django.core.exceptions import ImproperlyConfigured

from geonode import qgis_server


def validate_django_settings():
    """Check that settings file configured correctly for qgis_server backend.
    """
    # geonode.qgis_server must exists in INSTALLED_APPS and not geoserver
    if 'geonode.qgis_server' not in settings.INSTALLED_APPS:
        raise ImproperlyConfigured(
            'geonode.qgis_server module not included in INSTALLED_APPS.')
    if 'geonode.geoserver' in settings.INSTALLED_APPS:
        raise ImproperlyConfigured(
            'You want to use QGIS Server backend, but geonode.geoserver module'
            ' is still included in INSTALLED_APPS.')

    # LOCAL_GEOSERVER settings should not exists
    if hasattr(settings, 'LOCAL_GEOSERVER'):
        raise ImproperlyConfigured(
            "This setting will not be used when using QGIS Server backend.")

    # Should not include geoserver context_processor
    geoserver_context_processor = \
        'geonode.geoserver.context_processors.geoserver_urls'

    context_processors = settings.TEMPLATES[
        0]['OPTIONS']['context_processors']

    # Should include qgis_server context_processor
    qgis_server_context_processor = \
        'geonode.qgis_server.context_processors.qgis_server_urls'

    if geoserver_context_processor in context_processors:
        raise ImproperlyConfigured(
            'Geoserver context_processors should be excluded.')

    if qgis_server_context_processor not in context_processors:
        raise ImproperlyConfigured(
            'QGIS Server context_processors should be included.')

    if not hasattr(settings, 'QGIS_SERVER_URL'):
        raise ImproperlyConfigured(
            'QGIS_SERVER_URL setting should be configured.')

    if not hasattr(settings, 'QGIS_SERVER_CONFIG'):
        raise ImproperlyConfigured(
            'QGIS_SERVER_CONFIG setting should be configured.')

    if not settings.LAYER_PREVIEW_LIBRARY == 'leaflet':
        raise ImproperlyConfigured(
            'QGIS Server at the moment only works with '
            'LAYER_PREVIEW_LIBRARY = leaflet.')

    # Check OGC Server settings
    default_ogc_backend = settings.OGC_SERVER['default']

    if not default_ogc_backend['BACKEND'] == qgis_server.BACKEND_PACKAGE:
        raise ImproperlyConfigured(
            "OGC_SERVER['default']['BACKEND'] should be set to "
            "{package}.".format(package=qgis_server.BACKEND_PACKAGE))

    return True
