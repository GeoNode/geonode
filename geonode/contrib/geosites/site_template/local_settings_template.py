# flake8: noqa
# -*- coding: utf-8 -*-

###############################################
# Geosite local settings
###############################################
import os

# Outside URL
SITEURL = 'http://$DOMAIN'

OGC_SERVER['default']['LOCATION'] = os.path.join(GEOSERVER_URL, 'geoserver/')
OGC_SERVER['default']['PUBLIC_LOCATION'] = os.path.join(SITEURL, 'geoserver/')

# databases unique to site if not defined in site settings
"""
SITE_DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, '../development.db'),
    },
}
"""
