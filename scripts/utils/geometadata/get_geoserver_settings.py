#!/usr/bin/env python

from geonode.settings import GEONODE_APPS
import geonode.settings as settings
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geonode.settings')

print settings.OGC_SERVER['default']['USER'], \
    settings.OGC_SERVER['default']['PASSWORD'], \
    settings.SITEURL, \
    settings.DATABASE_HOST, \
    settings.DATABASE_PORT, \
    settings.DATABASE_USER, \
    settings.DATABASE_PASSWORD, \
    settings.DATABASES['datastore']['NAME'], \
    settings.DATABASE_NAME, \
