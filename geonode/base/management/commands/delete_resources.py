#########################################################################
#
# Copyright (C) 2018 OSGeo
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

import os
import json

# import needed to resolve model filters:
from django.db import transaction, IntegrityError
from django.core.management.base import BaseCommand, CommandError

from geonode.maps.models import Map
from geonode.layers.models import Dataset
from geonode.documents.models import Document


class Command(BaseCommand):

    help = 'Delete resources meeting a certain condition'

    def add_arguments(self, parser):

        parser.add_argument(
            '-c',
            '--config',
            dest='config_path',
            help='Configuration file path. Default is: delete_resources.json')

        parser.add_argument(
            '-l',
            '--dataset_filters',
            dest='dataset_filters',
            nargs='+',
            required=False,
        )

        parser.add_argument(
            '-m',
            '--map_filters',
            dest='map_filters',
            nargs='+',
            required=False,
        )

        parser.add_argument(
            '-d',
            '--document_filters',
            dest='document_filters',
            nargs='+',
            required=False,
        )

    def handle(self, **options):
        dataset_filters = options.get('dataset_filters')
        map_filters = options.get('map_filters')
        document_filters = options.get('document_filters')

        config_path = options.get('config_path')

        # check argument set
        if all(config is None for config in {dataset_filters, map_filters, document_filters, config_path}):
            raise CommandError(
                "No configuration provided. Please specify any of the following arguments: '-l', '-m', '-d', '-c'.")

        if any([dataset_filters, map_filters, document_filters]) and config_path:
            raise CommandError(
                "Too many configuration options provided. Please use either '-c' or '-l', '-m', '-d' arguments.")

        # check config_file, if it exists
        if config_path:

            if not os.path.exists(config_path):
                raise CommandError(f'Specified configuration file does not exist: "{config_path}"')

            if os.path.getsize(config_path) == 0:
                raise CommandError(f'Specified configuration file is empty: "{config_path}"')

            with open(config_path) as file:
                try:
                    config = json.load(file)
                except json.decoder.JSONDecodeError as e:
                    raise CommandError(f'Parsing configuration file failed with an exception: {e}')

                if (
                        # if config is an empty JSON object
                        not config
                        # or 'filters' is not set in config OR it is not an JSON object
                        or not isinstance(config.get('filters'), dict)
                        # or all filters are empty
                        or not any(
                            [
                                config.get('filters').get('dataset'),
                                config.get('filters').get('map'),
                                config.get('filters').get('document')
                            ])
                ):
                    print('Nothing to be done... exiting delete_resources command.')
                    return

            # override filters variables with configuration file data
            dataset_filters = config.get('filters').get('dataset')
            map_filters = config.get('filters').get('map')
            document_filters = config.get('filters').get('document')

        # remove layers
        if dataset_filters:

            if '*' in dataset_filters:
                layers_to_delete = Dataset.objects.all()
            else:
                layers_q_expressions = [eval(expr) for expr in dataset_filters]
                layers_to_delete = Dataset.objects.filter(*layers_q_expressions)

            for layer in layers_to_delete:
                print(f'Deleting layer "{layer.name}" with ID: {layer.id}')
                try:
                    with transaction.atomic():
                        layer.delete()
                except IntegrityError:
                    raise

        if map_filters:

            if '*' in map_filters:
                maps_to_delete = Map.objects.all()
            else:
                maps_q_expressions = [eval(expr) for expr in map_filters]
                maps_to_delete = Map.objects.filter(*maps_q_expressions)

            for map in maps_to_delete:
                print(f'Deleting map "{map.title}" with ID: {map.id}')
                map.maplayers.all().delete()
                map.delete()

        if document_filters:

            if '*' in document_filters:
                documents_to_delete = Document.objects.all()
            else:
                documents_q_expressions = [eval(expr) for expr in document_filters]
                documents_to_delete = Document.objects.filter(*documents_q_expressions)

            for document in documents_to_delete:
                print(f'Deleting document "{document.title}" with ID: {document.id}')
                document.delete()
