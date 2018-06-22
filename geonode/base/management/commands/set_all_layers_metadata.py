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
from geonode.catalogue.models import catalogue_post_save


class Command(BaseCommand):
    """Resets Permissions to Public for All Layers
    """

    def handle(self, *args, **options):
        all_layers = Layer.objects.all()

        for index, layer in enumerate(all_layers):
            print "[%s / %s] Updating Layer [%s] ..." % ((index + 1), len(all_layers), layer.name)
            try:
                catalogue_post_save(instance=layer, sender=layer.__class__)
            except:
                # import traceback
                # traceback.print_exc()
                print "[ERROR] Layer [%s] couldn't be updated" % (layer.name)
