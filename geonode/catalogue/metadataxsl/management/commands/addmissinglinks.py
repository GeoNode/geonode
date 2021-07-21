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

from geonode.base.models import Link, ResourceBase
from geonode.catalogue.metadataxsl.models import add_xsl_link


class Command(BaseCommand):
    help = 'Add missing links to ISO XSL metadata service'

    def handle(self, *args, **options):

        for resource in ResourceBase.objects.all():
            print(f'Checking resource with id {resource.id}')

            # check ISO link exists
            isolink = Link.objects.filter(resource_id=resource.id, link_type='metadata', name='ISO')
            if isolink:
                print(f'  ISO link found for resource {resource.id} "{resource.title}"')
                created = add_xsl_link(resource)
                if created:
                    print('   XSL link created')
            else:
                print(f'  ISO link NOT found for resource {resource.id} "{resource.title}"')
