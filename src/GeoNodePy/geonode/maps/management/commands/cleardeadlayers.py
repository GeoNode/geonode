from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import pre_delete
from geonode.maps.models import Layer, delete_layer
from urllib2 import URLError

class Command(BaseCommand):
    help = 'Update the GeoNode application with data from GeoServer'
    args = '[none]'

    @transaction.commit_on_success()
    def handle(self, *args, **keywordargs):
        try:
            pre_delete.disconnect(delete_layer, sender=Layer)
            cat = Layer.objects.gs_catalog
            storenames = [s.name for s in cat.get_stores()]
            layernames = [l.name for l in cat.get_resources()]
            for l in Layer.objects.all():
                if l.store not in storenames or l.name not in layernames:
                    l.delete()
                    print l
        except URLError:
            print "Couldn't connect to GeoServer; is it running? Make sure the GEOSERVER_BASE_URL setting is set correctly."
        finally:
            pre_delete.connect(delete_layer, sender=Layer)
