from django.core.management.base import BaseCommand
from geonode.maps.models import Layer
from urllib2 import URLError

class Command(BaseCommand):
    help = 'Update GeoNode layer srs, bbox, llbox properties with data from GeoServer'
    args = '[none]'

    def handle(self, *args, **keywordargs):
        try:
            Layer.objects.update_bboxes()
        except URLError:
            print "Couldn't connect to GeoServer; is it running? Make sure the GEOSERVER_BASE_URL setting is set correctly."