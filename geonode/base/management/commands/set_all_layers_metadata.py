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

from geonode.geoserver.helpers import ogc_server_settings
from django.core.management.base import BaseCommand
from geonode.base.models import Link
from geonode.layers.models import Layer
from geonode.catalogue.models import catalogue_post_save

from geonode import geoserver, qgis_server  # noqa
from geonode.utils import check_ogc_backend, set_resource_default_links

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    from geonode.geoserver.helpers import set_attributes_from_geoserver as set_attributes
elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    from geonode.qgis_server.gis_tools import set_attributes

_names = ['Zipped Shapefile', 'Zipped', 'Shapefile', 'GML 2.0', 'GML 3.1.1', 'CSV',
          'GeoJSON', 'Excel', 'Legend', 'GeoTIFF', 'GZIP', 'Original Dataset',
          'ESRI Shapefile', 'View in Google Earth', 'KML', 'KMZ', 'Atom', 'DIF',
          'Dublin Core', 'ebRIM', 'FGDC', 'ISO', 'ISO with XSL']


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
            print "[%s / %s] Updating Layer [%s] ..." % ((index + 1), len(all_layers), layer.name)
            try:
                # recalculate the layer statistics
                set_attributes(layer, overwrite=True)

                # refresh metadata links
                set_resource_default_links(layer, layer, prune=False)

                # refresh catalogue metadata records
                catalogue_post_save(instance=layer, sender=layer.__class__)

                if remove_duplicates:
                    # remove duplicates
                    for _n in _names:
                        _links = Link.objects.filter(resource__id=layer.id, name=_n)
                        while _links.count() > 1:
                            _links.last().delete()
                            print '.',
                    # fixup Legend links
                    legend_url_template = ogc_server_settings.PUBLIC_LOCATION + \
                        'ows?service=WMS&request=GetLegendGraphic&format=image/png&WIDTH=20&HEIGHT=20&LAYER=' + \
                        '{alternate}&STYLE={style_name}' + \
                        '&legend_options=fontAntiAliasing:true;fontSize:12;forceLabels:on'
                    if layer.default_style and not layer.get_legend_url(style_name=layer.default_style.name):
                        Link.objects.update_or_create(
                            resource=layer.resourcebase_ptr,
                            name='Legend',
                            extension='png',
                            url=legend_url_template.format(
                                alternate=layer.alternate,
                                style_name=layer.default_style.name),
                            mime='image/png',
                            link_type='image')
            except BaseException as e:
                import traceback
                traceback.print_exc()
                if ignore_errors:
                    print "[ERROR] Layer [%s] couldn't be updated" % (layer.name)
                else:
                    raise e
