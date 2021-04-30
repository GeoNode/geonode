# -*- coding: utf-8 -*-
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
from geonode import geoserver  # noqa
from geonode.catalogue.models import catalogue_post_save
from geonode.geoserver.helpers import ogc_server_settings
import logging


logger = logging.getLogger(__name__)


from geonode.utils import (
    check_ogc_backend,
    set_resource_default_links
)
from geonode.base.utils import (
    delete_orphaned_thumbs,
    remove_duplicate_links
)

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    from geonode.geoserver.helpers import set_attributes_from_geoserver as set_attributes


class Command(BaseCommand):
    help = 'Resets Metadata Attributes and Schema to All Layers'

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
            '-d',
            '--remove-duplicates',
            action='store_true',
            dest='remove_duplicates',
            default=False,
            help='Remove duplicates first.'
        )
        parser.add_argument(
            '-p',
            '--prune',
            action='store_true',
            dest='prune',
            default=False,
            help='Prune Old Links.'
        )
        parser.add_argument(
            '-t',
            '--delete-orphaned-thumbs',
            action='store_true',
            dest='delete_orphaned_thumbnails',
            default=False,
            help='Delete Orphaned Thumbnails.'
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
        remove_duplicates = options.get('remove_duplicates')
        prune = options.get('prune')
        delete_orphaned_thumbnails = options.get('delete_orphaned_thumbnails')
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
            print(f"[{index + 1} / {len(all_layers)}] Updating Layer [{layer.name}] ...")
            try:
                # recalculate the layer statistics
                set_attributes(layer, overwrite=True)

                # refresh metadata links
                set_resource_default_links(layer, layer, prune=prune)

                # refresh catalogue metadata records
                catalogue_post_save(instance=layer, sender=layer.__class__)

                # remove duplicates
                if remove_duplicates:
                    remove_duplicate_links(layer)
            except Exception as e:
                import traceback
                traceback.print_exc()
                if ignore_errors:
                    logger.error(f"[ERROR] Layer [{layer.name}] couldn't be updated")
                else:
                    raise e

        # delete orphaned thumbs
        if delete_orphaned_thumbnails:
            delete_orphaned_thumbs()
