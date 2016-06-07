# flake8: noqa
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

##### Settings to be included first

# Default Django settings for GeoNode.
import os
import geonode
GEONODE_ROOT = os.path.realpath(os.path.dirname(geonode.__file__))
execfile(os.path.join(GEONODE_ROOT, 'settings.py'))

# project location
PROJECT_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))

# site location (current settings file)
SITE_ROOT = os.path.realpath(os.path.dirname(__file__))

###############################################
# Master Geosite settings
###############################################

TIME_ZONE = 'America/New_York'

# Directory where static and media files will be served from
SERVE_PATH = ''

# Key of database to be used as datastore for GeoServer
DATASTORE = ''

# override urls for individual sites if needed
ROOT_URLCONF = 'geonode.contrib.geosites.urls'

INSTALLED_APPS = INSTALLED_APPS + ('geonode.contrib.geosites',)

# put development database in common location for all sites
DATABASES['default']['NAME'] = os.path.join(SITE_ROOT, '..', 'development.db')

# internal url to GeoServer
GEOSERVER_URL = 'http://localhost:8080/geoserver/'

##### Global Overrides
# Below are some common GeoNode settings that might be overridden to provide
# global setting acrosss all sites. Can be overridden in a sites settings.

# admin email
#THEME_ACCOUNT_CONTACT_EMAIL = ''

# globally installed apps
#INSTALLED_APPS = () + INSTALLED_APPS

# Common to globally allow specific document size (GeoNode default is 2)
#MAX_DOCUMENT_SIZE = 10

# If sites are subdomains of .domain can allow them all here
# e.g. '.geonode.org' will allow all subdomains of geonode.org
#PROXY_ALLOWED_HOSTS = ('.domain',)


##### Production settings

# DEBUG Settings
DEBUG = True
TEMPLATE_DEBUG = DEBUG
DEBUG_TOOLBAR = False

##### Read in local_settings
# Load more settings from a file called local_settings.py if it exists
try:
    from local_settings import *
except ImportError:
    pass

