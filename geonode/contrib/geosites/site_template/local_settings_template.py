# flake8: noqa
# -*- coding: utf-8 -*-

###############################################
# Geosite local settings
###############################################
import os

# Outside URL
SITEURL = 'http://$DOMAIN'


# databases unique to site if not defined in site settings
"""
SITE_DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, '../development.db'),
    },
}
"""

# update settings set in geonode settings now that some have been overwritten
# note next 2 lines will prevent dev server from running properly
OGC_SERVER['default']['PUBLIC_LOCATION'] = os.path.join(SITEURL, 'geoserver/')
CATALOGUE['default']['URL'] = '%scatalogue/csw' % SITEURL
PYCSW['CONFIGURATION']['metadata:main']['provider_url'] = SITEURL
LOCAL_GEOSERVER['source']['url'] = OGC_SERVER['default']['PUBLIC_LOCATION'] + 'wms'
