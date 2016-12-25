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

# Django settings for docker.
import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

from geonode.settings import *

# os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8000'
if 'DOCKER_HOST_IP' in os.environ:
    # set DJANGO_LIVE_TEST_SERVER_ADDRESS with docker host address
    os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = os.getenv(
        'DOCKER_HOST_IP') + ':' + os.getenv('PUBLIC_PORT')
else:
    os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8000'

if 'DOCKER_HOST_IP' in os.environ:
    # set ALLOWED_HOSTS with docker host address
    ALLOWED_HOSTS = os.getenv(
        'ALLOWED_HOSTS', ['localhost', 'django', os.getenv('DOCKER_HOST_IP')]
    )
else:
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', ['localhost', 'django'])

# SITEURL = os.getenv('SITEURL', "http://localhost:8000/")
if 'DOCKER_HOST_IP' in os.environ:
    # set siteurl with docker host address
    SITEURL = 'http://' + os.getenv(
        'DOCKER_HOST_IP') + ':' + os.getenv('PUBLIC_PORT') + '/'
else:
    SITEURL = os.getenv('SITEURL', "http://localhost:8000/")

#GEOSERVER_LOCATION = os.getenv(
#    'GEOSERVER_LOCATION', 'http://localhost:8080/geoserver/'
#)

if 'DOCKER_HOST_IP' in os.environ:
    GEOSERVER_LOCATION = os.getenv('GEOSERVER_INTERNAL_URL')
else:
    GEOSERVER_LOCATION = os.getenv(
        'GEOSERVER_LOCATION', 'http://localhost:8080/geoserver/'
    )

#GEOSERVER_PUBLIC_LOCATION = os.getenv(
#    'GEOSERVER_PUBLIC_LOCATION', 'http://localhost:8080/geoserver/'
#)
if 'DOCKER_HOST_IP' in os.environ:
    GEOSERVER_PUBLIC_LOCATION = 'http://' + os.getenv(
        'DOCKER_HOST_IP') + ':8080' + '/geoserver/'
else:
    GEOSERVER_PUBLIC_LOCATION = os.getenv(
        'GEOSERVER_PUBLIC_LOCATION', 'http://localhost:8080/geoserver/'
    )

import ipdb; ipdb.set_trace()
# OGC (WMS/WFS/WCS) Server Settings
# OGC (WMS/WFS/WCS) Server Settings
OGC_SERVER = {
    'default': {
        'BACKEND': 'geonode.geoserver',
        'LOCATION': GEOSERVER_LOCATION,
        'LOGIN_ENDPOINT': 'j_spring_oauth2_geonode_login',
        'LOGOUT_ENDPOINT': 'j_spring_oauth2_geonode_logout',
        # PUBLIC_LOCATION needs to be kept like this because in dev mode
        # the proxy won't work and the integration tests will fail
        # the entire block has to be overridden in the local_settings
        'PUBLIC_LOCATION': GEOSERVER_PUBLIC_LOCATION,
        'USER': 'admin',
        'PASSWORD': 'geoserver',
        'MAPFISH_PRINT_ENABLED': True,
        'PRINT_NG_ENABLED': True,
        'GEONODE_SECURITY_ENABLED': True,
        'GEOGIG_ENABLED': False,
        'WMST_ENABLED': False,
        'BACKEND_WRITE_ENABLED': True,
        'WPS_ENABLED': False,
        'LOG_FILE': '%s/geoserver/data/logs/geoserver.log'
        % os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir)),
        # Set to name of database in DATABASES dictionary to enable
        'DATASTORE': '',  # 'datastore',
        'PG_GEOGIG': False,
        'TIMEOUT': 10  # number of seconds to allow for HTTP requests
    }
}

# CSW settings
CATALOGUE = {
    'default': {
        # The underlying CSW implementation
        # default is pycsw in local mode (tied directly to GeoNode Django DB)
        'ENGINE': 'geonode.catalogue.backends.pycsw_local',
        # pycsw in non-local mode
        # 'ENGINE': 'geonode.catalogue.backends.pycsw_http',
        # GeoNetwork opensource
        # 'ENGINE': 'geonode.catalogue.backends.geonetwork',
        # deegree and others
        # 'ENGINE': 'geonode.catalogue.backends.generic',

        # The FULLY QUALIFIED base url to the CSW instance for this GeoNode
        'URL': '%scatalogue/csw' % SITEURL,
        # 'URL': 'http://localhost:8080/geonetwork/srv/en/csw',
        # 'URL': 'http://localhost:8080/deegree-csw-demo-3.0.4/services',

        # login credentials (for GeoNetwork)
        # 'USER': 'admin',
        # 'PASSWORD': 'admin',
    }
}

# pycsw settings
PYCSW = {
    # pycsw configuration
    'CONFIGURATION': {
        # uncomment / adjust to override server config system defaults
        # 'server': {
        #    'maxrecords': '10',
        #    'pretty_print': 'true',
        #    'federatedcatalogues': 'http://catalog.data.gov/csw'
        # },
        'metadata:main': {
            'identification_title': 'GeoNode Catalogue',
            'identification_abstract': 'GeoNode is an open source platform' \
            ' that facilitates the creation, sharing, and collaborative use' \
            ' of geospatial data',
            'identification_keywords': 'sdi, catalogue, discovery, metadata,' \
            ' GeoNode',
            'identification_keywords_type': 'theme',
            'identification_fees': 'None',
            'identification_accessconstraints': 'None',
            'provider_name': 'Organization Name',
            'provider_url': SITEURL,
            'contact_name': 'Lastname, Firstname',
            'contact_position': 'Position Title',
            'contact_address': 'Mailing Address',
            'contact_city': 'City',
            'contact_stateorprovince': 'Administrative Area',
            'contact_postalcode': 'Zip or Postal Code',
            'contact_country': 'Country',
            'contact_phone': '+xx-xxx-xxx-xxxx',
            'contact_fax': '+xx-xxx-xxx-xxxx',
            'contact_email': 'Email Address',
            'contact_url': 'Contact URL',
            'contact_hours': 'Hours of Service',
            'contact_instructions': 'During hours of service. Off on ' \
            'weekends.',
            'contact_role': 'pointOfContact',
        },
        'metadata:inspire': {
            'enabled': 'true',
            'languages_supported': 'eng,gre',
            'default_language': 'eng',
            'date': 'YYYY-MM-DD',
            'gemet_keywords': 'Utility and governmental services',
            'conformity_service': 'notEvaluated',
            'contact_name': 'Organization Name',
            'contact_email': 'Email Address',
            'temp_extent': 'YYYY-MM-DD/YYYY-MM-DD',
        }
    }
}

