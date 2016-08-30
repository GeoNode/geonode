from django.core.management.base import BaseCommand
from geonode.contrib.geosites.utils import add_site


class Command(BaseCommand):
    """ Creates new site based """

    can_import_settings = True

    def handle(self, *args, **kwargs):
        if len(args) < 2:
            raise Exception('Adding site requires name and site')
        add_site(args[0], args[1])
