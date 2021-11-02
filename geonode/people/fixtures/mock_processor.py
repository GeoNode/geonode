#########################################################################
# This is to mock the GEONODE_APPS_INSTALLED for test in geonode.people.tests.PeopleTest
#########################################################################
from django.conf import settings
from geonode import get_version
from geonode.catalogue import default_catalogue_backend
from django.contrib.sites.models import Site


def resource_urls(request):
    """Global values to pass to templates"""
    site = Site.objects.get_current()
    defaults = dict(
        STATIC_URL=settings.STATIC_URL,
        CATALOGUE_BASE_URL=default_catalogue_backend()['URL'],
        VERSION=get_version(),
        SITE_NAME=site.name,
        SITE_DOMAIN=site.domain,
        SITEURL=settings.SITEURL,
        INSTALLED_APPS=settings.INSTALLED_APPS,

        # GeoNode Apps
        GEONODE_APPS_ENABLE=getattr(settings, 'GEONODE_APPS_ENABLE', False),
        GEONODE_APPS_NAME=getattr(settings, 'GEONODE_APPS_NAME', 'Apps'),
        GEONODE_APPS_NAV_MENU_ENABLE=getattr(settings, 'GEONODE_APPS_NAV_MENU_ENABLE', False),
        REQ_THESAURI=[],
        GEONODE_APPS_INSTALLED=['Geoapp1']
    )
    return defaults
