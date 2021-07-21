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

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from oauth2_provider.models import Application
from oauth2_provider.generators import generate_client_id, generate_client_secret

from geonode import geoserver  # noqa
from geonode.utils import check_ogc_backend


class Command(BaseCommand):
    """Creates or updates the oauth2 Application
    """
    can_import_settings = True

    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            '-f',
            '--force',
            action='store_true',
            dest='force_exec',
            default=False,
            help='Forces the regeneration of OAUth keys.')

        parser.add_argument(
            '--target-address',
            dest='target_address',
            help='Target Address (the one to be changed e.g. http://my-public.geonode.org)')

    def handle(self, *args, **options):

        force_exec = options.get('force_exec')
        target_address = options.get('target_address')

        client_id = None
        client_secret = None

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            from geonode.geoserver.helpers import ogc_server_settings
            redirect_uris = f'{ogc_server_settings.LOCATION}\n{ogc_server_settings.public_url}\n{target_address}/geoserver/'  # noqa
            if Application.objects.filter(name='GeoServer').exists():
                Application.objects.filter(name='GeoServer').update(redirect_uris=redirect_uris)
                if force_exec:
                    Application.objects.filter(name='GeoServer').update(
                        client_id=generate_client_id(),
                        client_secret=generate_client_secret()
                    )
                app = Application.objects.filter(name='GeoServer')[0]
                client_id = app.client_id
                client_secret = app.client_secret
            else:
                client_id = generate_client_id()
                client_secret = generate_client_secret()
                Application.objects.create(
                    skip_authorization=True,
                    redirect_uris=redirect_uris,
                    name='GeoServer',
                    authorization_grant_type='authorization-code',
                    client_type='confidential',
                    client_id=client_id,
                    client_secret=client_secret,
                    user=get_user_model().objects.filter(is_superuser=True)[0]
                )
        return f'{client_id},{client_secret}'
