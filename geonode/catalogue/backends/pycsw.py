#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

from django.conf import settings
from geonode.catalogue.backends.generic import CatalogueBackend as GenericCatalogueBackend

class CatalogueBackend(GenericCatalogueBackend):
    def __init__(self, *args, **kwargs):
        super(CatalogueBackend, self).__init__(*args, **kwargs)
        self.catalogue.type = 'pycsw'
        self.catalogue.formats = ['Atom', 'DIF', 'Dublin Core', 'ebRIM', 'FGDC', 'TC211']

        self.catalogue.local = True
        if not settings.CATALOGUE['default']['LOCAL']:
            self.catalogue.local = False
