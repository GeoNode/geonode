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
import sys
import time
import logging

from geonode.services import enumerations
from geonode.services.models import Service
from geonode.base.models import ResourceBase
from geonode.base.management.commands import helpers
from geonode.harvesting.models import (
    Harvester,
    HarvestableResource,
    AsynchronousHarvestingSession)

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    This management command is meant to be used on old Remote Services not relying on Harvesters.

    The command will try to align the old Datasets linked to the Remote Service with the ones
    available from the Harvester.

    WARNING: The procedure may take some time.
    """

    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            '-f',
            '--force',
            action='store_true',
            dest='force_exec',
            default=False,
            help='Forces the execution without asking for confirmation.')

        parser.add_argument(
            '-u',
            '--url',
            dest="url",
            default=None,
            help="Checks only for the Services matching the specified base url.")

        parser.add_argument(
            '-p',
            '--prune',
            dest="prune",
            default=False,
            action='store_true',
            help="Prune old resources that could not be converted.")

    def handle(self, *args, console=sys.stdout, **options):
        force_exec = options.get('force_exec')
        filter = options.get('url')
        prune = options.get('prune')

        _services_with_empty_harvesters = Service.objects.filter(
            type__in=(enumerations.WMS, enumerations.GN_WMS),
            harvester__num_harvestable_resources=0)
        if filter:
            _services_with_empty_harvesters = _services_with_empty_harvesters.filter(
                base_url__icontains=filter)

        _count = _services_with_empty_harvesters.count()
        if _count == 0:
            print("No Service found!")
        else:
            _plural = 's' if _count > 1 else ''
            print(f"Found {_count} Service{_plural} to be converted:")
            _service_resources = {}
            for _s in _services_with_empty_harvesters.iterator():
                _service_resources[_s.name] = ResourceBase.objects.filter(
                    remote_typename=_s.name
                )
                print(f"  Base URL: {_s.base_url} - Available resources: {_service_resources[_s.name].count()}")
            message = 'You want to proceed?'

            if force_exec or helpers.confirm(prompt=message, resp=False):
                for _s in _services_with_empty_harvesters.iterator():
                    print(f" Now processing Service {_s.name}:")
                    print("   Initializing Harvester...")
                    _s.harvester.update_availability()
                    if _s.harvester.remote_available:
                        try:
                            _s.harvester.initiate_update_harvestable_resources()
                            while _s.harvester.latest_refresh_session.status == AsynchronousHarvestingSession.STATUS_ON_GOING:
                                time.sleep(2.0)
                            _harvester = Harvester.objects.get(id=_s.harvester.id)
                            print(f"   Done with harvestable resources: {_harvester.num_harvestable_resources}")
                            if _harvester.num_harvestable_resources == 0:
                                print(f"   {_harvester.num_harvestable_resources} available resources. No further processing!")
                            else:
                                print("   Searching for matching resources...")
                                _harvestable_resources = {
                                    _harvester.name: []
                                }
                                for _r in _service_resources[_s.name].iterator():
                                    if HarvestableResource.objects.filter(title=_r.title).exists():
                                        _harvestable_resources[_harvester.name].append(
                                            (
                                                _r,
                                                HarvestableResource.objects.filter(title=_r.title).get()
                                            )
                                        )
                                print(f"   Done with matching resources: {len(_harvestable_resources[_harvester.name])}")
                                if len(_harvestable_resources[_harvester.name]) == 0:
                                    print(f"   {len(_harvestable_resources[_harvester.name])} matching resources. No further processing!")
                                else:
                                    for _matching_resources in _harvestable_resources[_harvester.name]:
                                        _r, _h_r = _matching_resources
                                        print(f"   Processing resource {_r.title}...")
                                        try:
                                            _h_r.geonode_resource = _r
                                            _h_r.should_be_harvested = True
                                            _h_r.remote_resource_type = _r.resource_type
                                            _h_r.save()
                                        except Exception as e:
                                            print(f"   There was an error trying to upgrade the Resource {_r.title}: {e}")
                                            if prune:
                                                print(f"   Pruning the failing Resource {_r.title}...")
                                                ResourceBase.objects.filter(title=_r.title).delete()
                                                print("   Done.")
                                    print("   Done.")
                        except Exception as e:
                            print(f"   There was an error trying to upgrade the Service {_s.name}: {e}")
                            _s.harvester.status = Harvester.STATUS_READY
                            _s.harvester.num_harvestable_resources = 0
                            _s.harvester.save()
                    else:
                        print("   Done. Unfortunately the remote endpoint is not available.")
