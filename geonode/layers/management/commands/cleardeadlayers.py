#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import pre_delete
from geonode.layers.models import Layer, geoserver_pre_delete

from urllib2 import URLError


class Command(BaseCommand):
    help = """
    Identifies and removes layers in the Django app which don't correspond to
    layers in the GeoServer catalog.  Such layers were created by an
    error-handling bug in GeoNode 1.0-RC2 and earlier.
    """
    args = '[none]'

    @transaction.commit_on_success()
    def handle(self, *args, **keywordargs):
        try:
            pre_delete.disconnect(geoserver_pre_delete, sender=Layer)
            cat = Layer.objects.gs_catalog
            storenames = [s.name for s in cat.get_stores()]
            layernames = [l.name for l in cat.get_resources()]
            for l in Layer.objects.all():
                if l.store not in storenames or l.name not in layernames:
                    l.delete()
                    print '[cleared] Layer %s' % l
        except URLError:
            print "Couldn't connect to GeoServer; is it running? Make sure the GEOSERVER_BASE_URL setting is set correctly."
        finally:
            pre_delete.connect(geoserver_pre_delete, sender=Layer)
