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

from geonode.layers.models import Layer
from django.core.management.base import BaseCommand
from requests.auth import HTTPBasicAuth
from defusedxml import lxml as dlxml
import xml.etree.ElementTree as ET
from django.conf import settings
from lxml import etree
import requests


class Command(BaseCommand):
    help = 'Assign all the default values to GeoServer Gridsets'

    def add_arguments(self, parser):
        pass

    def handle(self, **options):
        try:
            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']
            """
            curl -v -u admin:geoserver -XGET \
                "http://<host>:<port>/geoserver/gwc/rest/layers/geonode:tasmania_roads.xml"
            """
            layers = Layer.objects.all()
            print(f"Total layers to be updated: {layers.count()}")
            for layer in layers:
                print(f"Processing layer: {layer.typename}")
                r = requests.get(f'{url}gwc/rest/layers/{layer.typename}.xml',
                                 auth=HTTPBasicAuth(user, passwd))

                if (r.status_code < 200 or r.status_code > 201):
                    print(f"Layer does not exists on geoserver: {layer.name}")
                    continue
                try:
                    xml_content = r.content
                    tree = dlxml.fromstring(xml_content)

                    gwc_id = tree.find('id')
                    tree.remove(gwc_id)

                    gwc_gridSubsets = tree.find('gridSubsets')
                    if len(gwc_gridSubsets) == 6:
                        continue

                    tree.remove(gwc_gridSubsets)
                    gwc_gridSubsets = etree.Element('gridSubsets')
                    for gridSubset in ('EPSG:3857', 'EPSG:3857x2', 'EPSG:4326', 'EPSG:4326x2', 'EPSG:900913', 'EPSG:900913x2'):
                        gwc_gridSubset = etree.Element('gridSubset')
                        gwc_gridSetName = etree.Element('gridSetName')
                        gwc_gridSetName.text = gridSubset
                        gwc_gridSubset.append(gwc_gridSetName)
                        gwc_gridSubsets.append(gwc_gridSubset)

                    tree.append(gwc_gridSubsets)

                    """
                    curl -v -u admin:geoserver -XPOST \
                        -H "Content-type: text/xml" -d @poi.xml \
                            "http://localhost:8080/geoserver/gwc/rest/layers/tiger:poi.xml"
                    """
                    headers = {'Content-type': 'text/xml'}
                    payload = ET.tostring(tree)
                    r = requests.post(f'{url}gwc/rest/layers/{layer.typename}.xml',
                                      headers=headers,
                                      data=payload,
                                      auth=HTTPBasicAuth(user, passwd))
                    if (r.status_code < 200 or r.status_code > 201):
                        print(f"Error during update of layer in geoserver: {layer.name} {r.content}")
                        continue
                except Exception as e:
                    raise e
        except Exception as e:
            raise e
