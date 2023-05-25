# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2023 OSGeo
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

import logging
import requests
from requests.auth import HTTPBasicAuth

from django.core.management.base import BaseCommand
from django.conf import settings

from geonode.layers.models import Dataset


logger = logging.getLogger(__name__)


REQ_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<GeoServerLayer>
   <enabled>true</enabled>
   <inMemoryCached>true</inMemoryCached>
   <name>{}</name>
   <metaWidthHeight>
      <int>2</int>
      <int>1</int>
   </metaWidthHeight>
   <mimeFormats>
      <string>application/json;type=utfgrid</string>
      <string>image/png</string>
      <string>image/vnd.jpeg-png</string>
      <string>image/jpeg</string>
      <string>image/vnd.jpeg-png8</string>
      <string>image/gif</string>
      <string>image/png8</string>
   </mimeFormats>
   <gridSubsets>
      <gridSubset>
         <gridSetName>EPSG:3857</gridSetName>
      </gridSubset>
      <gridSubset>
         <gridSetName>EPSG:3857x2</gridSetName>
      </gridSubset>
      <gridSubset>
         <gridSetName>EPSG:4326</gridSetName>
      </gridSubset>
      <gridSubset>
         <gridSetName>EPSG:4326x2</gridSetName>
      </gridSubset>
      <gridSubset>
         <gridSetName>EPSG:900913</gridSetName>
      </gridSubset>
   </gridSubsets>
</GeoServerLayer>"""


class Command(BaseCommand):
    help = "Create missing TileLayers in GWC"

    def add_arguments(self, parser):
        pass

    def handle(self, **options):
        try:
            baseurl = settings.OGC_SERVER["default"]["LOCATION"]
            user = settings.OGC_SERVER["default"]["USER"]
            passwd = settings.OGC_SERVER["default"]["PASSWORD"]
            """
            curl -v -u admin:geoserver -XGET \
                "http://<host>:<port>/geoserver/gwc/rest/layers/geonode:tasmania_roads.xml"
            """
            layers = Dataset.objects.all()
            tot = len(layers)
            logger.info(f"Total layers in GeoNode: {tot}")
            i = 0
            cnt_old = 0
            cnt_new = 0
            cnt_bad = 0
            for layer in layers:
                i += 1
                logger.info(f"- {i}/{tot} Processing layer: {layer.typename}")
                r = requests.get(f"{baseurl}gwc/rest/layers/{layer.typename}.xml", auth=HTTPBasicAuth(user, passwd))

                if r.status_code == 200:
                    logger.info("  - Layer already configured")
                    cnt_old += 1
                    continue
                try:
                    data = REQ_TEMPLATE.format(layer.name)
                    url = f"{baseurl}gwc/rest/layers/{layer.typename}.xml"
                    logger.info("  - Configuring...")
                    response = requests.put(
                        url, data=data, headers={"Content-Type": "text/xml"}, auth=HTTPBasicAuth(user, passwd)
                    )

                    if response.status_code == 200:
                        logger.info(f"  - Done {layer.name}")
                        cnt_new += 1
                    else:
                        logger.warning(f"Layer {layer.typename} couldn't be configured: code {response.status_code}")
                        cnt_bad += 1

                except Exception as e:
                    raise e
        except Exception as e:
            raise e

        logger.info("Work completed")
        logger.info(f"- TileLayers configured: {cnt_new}")
        logger.info(f"- TileLayers in error  : {cnt_bad}")
        logger.info(f"- TileLayers found     : {cnt_old}")
