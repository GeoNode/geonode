# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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
from geonode.qgis_server.helpers import style_list


class Command(BaseCommand):
    help = ("Import QGIS Server styles associated with layers.")

    def handle(self, *args, **options):
        layers = Layer.objects.all()

        for l in layers:
            try:
                l.qgis_layer
            except Exception:
                print(f"Layer {l.name} has no associated qgis_layer")
                continue

            if l.qgis_layer:
                print("Fetching styles for layer %s".format(l.name))

                try:
                    styles = style_list(l, internal=False)
                except Exception:
                    print("Failed to fetch styles")
                    continue

                print("Successfully fetch %d style(s)\n".format(len(styles)))
