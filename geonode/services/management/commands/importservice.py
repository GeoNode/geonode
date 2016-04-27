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
from optparse import make_option
from geonode.services.models import Service
from geonode.services.views import _register_cascaded_service, _register_indexed_service, \
    _register_harvested_service, _register_cascaded_layers, _register_indexed_layers
import json
from geonode.people.utils import get_valid_user
import sys


class Command(BaseCommand):

    help = 'Import a remote map service into GeoNode'
    option_list = BaseCommand.option_list + (

        make_option('-o', '--owner', dest="owner", default=None,
                    help="Name of the user account which should own the imported layers"),
        make_option('-r', '--registerlayers', dest="registerlayers", default=False,
                    help="Register all layers found in the service"),
        make_option('-u', '--username', dest="username", default=None,
                    help="Username required to login to this service if any"),
        make_option('-p', '--password', dest="password", default=None,
                    help="Username required to login to this service if any"),
        make_option('-s', '--security', dest="security", default=None,
                    help="Security permissions JSON - who can view/edit"),
    )

    args = 'url name type method'

    def handle(self, url, name, type, method, console=sys.stdout, **options):
        user = options.get('user')
        owner = get_valid_user(user)
        register_layers = options.get('registerlayers')
        username = options.get('username')
        password = options.get('password')
        perm_spec = options.get('permspec')

        register_service = True

        # First Check if this service already exists based on the URL
        base_url = url
        try:
            service = Service.objects.get(base_url=base_url)
        except Service.DoesNotExist:
            service = None
        if service is not None:
            print "This is an existing Service"
            register_service = False
            # Then Check that the name is Unique
        try:
            service = Service.objects.get(name=name)
        except Service.DoesNotExist:
            service = None
        if service is not None:
            print "This is an existing service using this name.\nPlease specify a different name."
        if register_service:
            if method == 'C':
                response = _register_cascaded_service(type, url, name, username, password, owner=owner, verbosity=True)
            elif method == 'I':
                response = _register_indexed_service(type, url, name, username, password, owner=owner, verbosity=True)
            elif method == 'H':
                response = _register_harvested_service(url, name, username, password, owner=owner, verbosity=True)
            elif method == 'X':
                print 'Not Implemented (Yet)'
            elif method == 'L':
                print 'Local Services not configurable via API'
            else:
                print 'Invalid method'

            json_response = json.loads(response.content)
            if "id" in json_response:
                print "Service created with id of %d" % json_response["id"]
                service = Service.objects.get(id=json_response["id"])
            else:
                print "Something went wrong: %s" % response.content
                return

            print service.id
            print register_layers

        if service and register_layers:
            layers = []
            for layer in service.layer_set.all():
                layers.append(layer.typename)
            if service.method == 'C':
                response = _register_cascaded_layers(user, service, layers, perm_spec)
            elif service.method == 'I':
                response = _register_indexed_layers(user, service, layers, perm_spec)
            elif service.method == 'X':
                print 'Not Implemented (Yet)'
            elif service.method == 'L':
                print 'Local Services not configurable via API'
            else:
                print('Invalid Service Type')

        print response.content
