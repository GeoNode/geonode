from django.core.management.base import BaseCommand
from geonode.maps.models import Layer
from urllib2 import URLError

class Command(BaseCommand):
    help = 'Import a specific layer from GeoServer into GeoNode'
    args = '<GeoServer layer resource name>'

    def handle(self, *args, **keywordargs):
        try:
            Layer.objects.import_existing_layer(args[0])
        except URLError:
            print "Couldn't connect to GeoServer/GeoNetwork; are they running? Make sure the settings for them are correct."
  