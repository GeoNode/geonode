# -*- coding: utf-8 -*-

###############################################
# Geosite settings
###############################################

import os
from geonode.contrib import geosites

# Directory of master site
GEOSITES_ROOT = os.path.dirname(geosites.__file__)
SITE_ROOT = os.path.dirname(__file__)

try:
    # read in project pre_settings
    execfile(os.path.join(SITE_ROOT, '../', 'pre_settings.py'))
except:
    # if not available, read in GeoSites pre_settings
    execfile(os.path.join(GEOSITES_ROOT, 'pre_settings.py'))

SITE_ID = $SITE_ID  # flake8: noqa
SITE_NAME = '$SITE_NAME'
# Should be unique for each site
SECRET_KEY = "fbk3CC3N6jt1AU9mGIcI"

# site installed apps
SITE_APPS = ()

# Site specific databases
SITE_DATABASES = {}

# Overrides

# Below are some common GeoNode settings that might be overridden for site

# base urls for all sites
# ROOT_URLCONF = 'projectname.urls'

# admin email
# THEME_ACCOUNT_CONTACT_EMAIL = ''

# Have GeoServer use this database for this site
# DATASTORE = ''

# Allow users to register
# REGISTRATION_OPEN = True

# Read in GeoSites post_settings
try:
    # read in project pre_settings
    execfile(os.path.join(SITE_ROOT, '../', 'post_settings.py'))
except:
    # if not available, read in GeoSites pre_settings
    execfile(os.path.join(GEOSITES_ROOT, 'post_settings.py'))
