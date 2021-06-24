#########################################################################
#
# Copyright (C) 2017 OSGeo
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
from geonode.layers.models import Layer
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Resets Permissions to Public for All Layers'

    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            '--ignore-errors',
            action='store_true',
            dest='ignore_errors',
            default=False,
            help='Stop after any errors are encountered.'
        )
        parser.add_argument(
            '-f',
            '--filter',
            dest="filter",
            default=None,
            help="Only update data the layers that match the given filter"),
        parser.add_argument(
            '-u',
            '--username',
            dest="username",
            default=None,
            help="Only update data owned by the specified username")

    def handle(self, *args, **options):
        ignore_errors = options.get('ignore_errors')
        filter = options.get('filter')
        if not options.get('username'):
            username = None
        else:
            username = options.get('username')

        all_layers = Layer.objects.all().order_by('name')
        if filter:
            all_layers = all_layers.filter(name__icontains=filter)
        if username:
            all_layers = all_layers.filter(owner__username=username)

        for index, layer in enumerate(all_layers):
            logger.info(f"[{(index + 1)} / {len(all_layers)}] Checking 'alternate' of Layer [{layer.name}] ...")
            try:
                if not layer.alternate:
                    layer.alternate = layer.typename
                    layer.save()
            except Exception as e:
                if ignore_errors:
                    logger.error(f"[ERROR] Layer [{layer.name}] couldn't be updated")
                else:
                    raise e
