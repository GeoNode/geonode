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
from oauth2_provider.models import Application
from oauth2_provider.generators import generate_client_id, generate_client_secret
from geonode.people.models import Profile


class Command(BaseCommand):
    """Creates or updates the oauth2 Application
    """
    can_import_settings = True

    def handle(self, *args, **options):
        from django.conf import settings
        client_id = None
        client_secret = None
        if 'geonode.geoserver' in settings.INSTALLED_APPS:
            from geonode.geoserver.helpers import ogc_server_settings
            if Application.objects.filter(name='GeoServer').exists():
                Application.objects.filter(name='GeoServer').update(redirect_uris=ogc_server_settings.public_url)
                app = Application.objects.filter(name='GeoServer')[0]
                client_id = app.client_id
                client_secret = app.client_secret
            else:
                client_id = generate_client_id()
                client_secret = generate_client_secret()
                Application.objects.create(
                    skip_authorization=True,
                    redirect_uris=ogc_server_settings.public_url,
                    name='GeoServer',
                    authorization_grant_type='authorization-code',
                    client_type='confidential',
                    client_id=client_id,
                    client_secret=client_secret,
                    user=Profile.objects.filter(is_superuser=True)[0]
                )
        return '%s,%s' % (client_id, client_secret)
