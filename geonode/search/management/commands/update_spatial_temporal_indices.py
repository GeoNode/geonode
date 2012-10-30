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
from geonode.maps.models import Map
from geonode.maps.models import Layer
import logging
from optparse import make_option
import traceback
import signal
import sys

def _handler(s,f):
    sys.exit(0)
signal.signal(signal.SIGINT,_handler)

class Command(BaseCommand):
    help = 'Update search indices'
    option_list = BaseCommand.option_list + (
        make_option('--update', dest="update", default=False, action="store_true",
            help="Update any existing entries"),
    )

    def handle(self, *args, **opts):
        logging.getLogger('geonode.search.models').setLevel(logging.DEBUG)
        update = opts['update']
        try:
            # if this is done at the top-level it can cause failures during
            # code-coverage
            from geonode.search.models import index_object
        except ImportError:
            print 'geodjango is most likely not enabled'
            return
        def index(o):
            try:
                index_object(o,update=update)
            except Exception:
                print 'error indexing', o
                traceback.print_exc()

        map(index,Map.objects.all())
        map(index,Layer.objects.all())
