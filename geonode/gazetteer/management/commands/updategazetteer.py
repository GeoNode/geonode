from django.core.management import BaseCommand
from geonode.gazetteer.models import GazetteerEntry
from geonode.maps.models import Layer


class Command(BaseCommand):
    help = """
    Assigns usernames to all gazetteer features that do not have an associated
    username yet.
    """
    args = '[none]'

    def handle(self, *args, **kwargs):
        gaz_layers = GazetteerEntry.objects.filter(
            username__isnull=True).values('layer_name').distinct()
        print ("Found %d layers in gazetteer with unasssigned users") % len(gaz_layers)
        for gl in gaz_layers:
            lname = gl['layer_name']
            try:
                layer = Layer.objects.get(name=lname)
                username = layer.owner.username
                print("Assigning features for %s to %s") % (layer.name, username)
                GazetteerEntry.objects.filter(
                    layer_name__exact=lname).update(username=username)
            except Layer.DoesNotExist:
                print("Layer %s no longer exists, removing from gazetteer" % lname)
                GazetteerEntry.objects.filter(layer_name__exact=lname).delete()
        print("Complete")
