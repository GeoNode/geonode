from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from urlparse import urlsplit


class Command(BaseCommand):
    """Overrides the default Site object with information from
       SITENAME and SITEURL
    """
    can_import_settings = True

    def handle(self, *args, **options):
        from django.conf import settings
        name = getattr(settings, 'SITENAME', 'GeoNode')
        url = getattr(settings, 'SITEURL')

        parsed = urlsplit(url)

        site = Site.objects.get_current()
        site.name = name
        site.domain = parsed.netloc
        site.save()
