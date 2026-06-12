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
import os
import xml.etree.ElementTree as ET

from django.core.management import CommandError

from geonode.base.management.command_utils import setup_logger
from geonode.geoserver.gwc import GWCClient
from geonode.layers.models import Dataset


logger = setup_logger()


class CreateTileLayers:
    help = "Create TileLayers in GWC"

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
            "--all",
            dest="create_all",
            action="store_true",
            help="Create caches for all layers",
        )

        parser.add_argument(
            "-t",
            "--template",
            dest="xmltemplatefilepath",
            help="Use the specified XML template file path",
        )

    def handle(self, **options):
        dry_run = options.get('dry-run')
        debug = options.get('debug')
        setup_logger(level=logging.DEBUG if debug else logging.INFO)

        force = options.get('force')

        requested_layers = options.get('layers', [])
        create_all = options.get('create_all')

        if not requested_layers and not create_all:
            raise CommandError("'create' command requires either the -l/--layer parameter(s) or the --all flag.")

        if requested_layers and create_all:
            raise CommandError("Cannot use both -l/--layer and --all at the same time.")

        xmltemplate = options.get('xmltemplatefilepath')

        if debug:
            logger.debug(f"FORCE is {force}")
            logger.debug(f"DRY-RUN is {dry_run}")
            logger.debug(f"LAYERS is {requested_layers}")

        self.run(requested_layers=requested_layers, create_all=create_all, force=force, xmltemplate=xmltemplate, dry_run=dry_run, debug=debug)

    def run(self, requested_layers=None, create_all=False, force=False, xmltemplate=None, dry_run=False, debug=False):
        if create_all:
            datasets_fields = Dataset.objects.values_list('typename', 'alternate')
            layer_names = [typename or alternate for typename, alternate in datasets_fields]
        else:
            layer_names = requested_layers
        tot = len(layer_names)
        logger.info(f"Total layers to be processed: {tot}")

        template = self.load_xml_template(xmltemplate, debug=debug)
        gwc = GWCClient(debug=debug)

        i = cnt_old = cnt_new = cnt_bad = cnt_force = 0

        for layername in layer_names:
            i += 1
            logger.info(f"- {i}/{tot} Processing layer: {layername}")

            r = gwc.get_layer(layername)
            if r.status_code == 200:
                if force:
                    logger.info("  - Forcing layer configuration in GWC")
                    cnt_force += 1
                else:
                    logger.info(f"  - Layer already configured in GWC (code {r.status_code})")
                    cnt_old += 1
                    continue
            try:
                logger.info("  - Configuring...")
                data = self.generate_xml(template, layername)
                if not dry_run:
                    response = gwc.set_layer(layername, data=data)

                if dry_run or response.status_code == 200:
                    logger.info(f"  - Done {layername}")
                    cnt_new += 1
                else:
                    logger.warning(f"Layer {layername} couldn't be configured: code {response.status_code}")
                    cnt_bad += 1

            except Exception as e:
                logger.warning(f"Error processing {layername}: {e}")
                cnt_bad += 1

        logger.info("Work completed")
        logger.info(f"- TileLayers configured: {cnt_new}" + (f" (forced {cnt_force})" if cnt_force else ""))
        logger.info(f"- TileLayers in error  : {cnt_bad}")
        logger.info(f"- TileLayers untouched : {cnt_old}")

    def load_xml_template(self, xmltemplate=None, debug=False):
        """Load the XML template"""
        if xmltemplate:
            logger.info(f"Using provided xml template at {xmltemplate}")
            xml_path = os.path.abspath(xmltemplate)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            xml_path = os.path.join(current_dir, "create_template.xml")

        if not os.path.isfile(xml_path):
            raise CommandError(f"XML template could not be found at {xml_path}")

        try:
            tree = ET.parse(xml_path)
        except ET.ParseError as e:
            if debug:
                logger.exception(f"Error parsing XML template {xml_path}")
            raise CommandError(f"Error parsing XML template {xml_path}: {e}")

        root = tree.getroot()
        return root

    def generate_xml(self, root, layer_name):
        name_node = root.find('name')

        if name_node is None:
            raise ValueError("name node not found in XML template")

        name_node.text = layer_name
        return ET.tostring(root, encoding="utf-8", method="xml")
