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
      <string>image/gif</string>
      <string>image/jpeg</string>
      <string>image/png</string>
      <string>image/png8</string>
      <string>image/vnd.jpeg-png</string>
      <string>image/vnd.jpeg-png8</string>
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
   <expireCache>0</expireCache>
   <expireClients>0</expireClients>
   <autoCacheStyles>true</autoCacheStyles>
   <gutter>0</gutter>
   <cacheWarningSkips/>
</GeoServerLayer>"""


class Command(BaseCommand):
    help = "Create missing TileLayers in GWC"

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            '--force',
            dest="force",
            action='store_true',
            help="Force tile layer re-creation also if it already exists in GWC")

        parser.add_argument(
            '-l',
            '--layer',
            dest="layers",
            action='append',
            help="Only process specified layers ")

        parser.add_argument(
            '-d',
            '--dry-run',
            dest="dry-run",
            action='store_true',
            help="Do not actually perform any change on GWC")

    def handle(self, **options):
        force = options.get('force')
        requested_layers = options.get('layers')
        dry_run = options.get('dry-run')

        logger.debug(f"FORCE is {force}")
        logger.debug(f"DRY-RUN is {dry_run}")
        logger.debug(f"LAYERS is {requested_layers}")

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
            cnt_skip = 0
            cnt_force = 0
            for layer in layers:
                i += 1
                logger.info(f"- {i}/{tot} Processing layer: {layer.typename}")

                if requested_layers and layer.typename not in requested_layers:
                    logger.info("  - Layer filtered out by args")
                    cnt_skip += 1
                    continue

                r = requests.get(f"{baseurl}gwc/rest/layers/{layer.typename}.xml", auth=HTTPBasicAuth(user, passwd))

                if r.status_code == 200:
                    if force:
                        logger.info("  - Forcing layer configuration in GWC")
                        cnt_force += 1
                    else:
                        logger.info("  - Layer already configured in GWC")
                        cnt_old += 1
                        continue
                try:
                    data = REQ_TEMPLATE.format(layer.name)
                    url = f"{baseurl}gwc/rest/layers/{layer.typename}.xml"
                    logger.info("  - Configuring...")

                    if not dry_run:
                        response = requests.put(
                            url, data=data, headers={"Content-Type": "text/xml"}, auth=HTTPBasicAuth(user, passwd)
                        )

                    if dry_run or response.status_code == 200:
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
        logger.info(f"- TileLayers configured: {cnt_new}" + (f" (forced {cnt_force})" if cnt_force else ""))
        logger.info(f"- TileLayers in error  : {cnt_bad}")
        logger.info(f"- TileLayers untouched : {cnt_old}")
        logger.info(f"- TileLayers skipped   : {cnt_skip}")
