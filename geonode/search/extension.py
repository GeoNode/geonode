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

from geonode.people.models import Profile 
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.search.util import resolve_extension

from django.conf import settings
import re

date_fmt = lambda dt: dt.isoformat()
USER_DISPLAY = 'User'
MAP_DISPLAY = 'Map'
LAYER_DISPLAY = 'Layer'
DOCUMENT_DISPLAY = 'Document'

# settings API
search_config = getattr(settings,'SIMPLE_SEARCH_SETTINGS', {})

exclude_patterns = search_config.get('layer_exclusions',[])

exclude_regex = [ re.compile(e) for e in exclude_patterns ]

process_results = resolve_extension('process_search_results')
if process_results is None:
    process_results = lambda r: r

owner_query = resolve_extension('owner_query')
if not owner_query:
    owner_query = lambda q: Profile.objects.filter(user__isnull=False)

owner_query_fields = resolve_extension('owner_query_fields') or []

layer_query = resolve_extension('layer_query')
if not layer_query:
    layer_query = lambda q: Layer.objects.filter()

map_query = resolve_extension('map_query')
if not map_query:
    map_query = lambda q: Map.objects.filter()

document_query = resolve_extension('document_query')
if not document_query:
    document_query = lambda q: Document.objects.filter()

display_names = resolve_extension('display_names')
if display_names:
    USER_DISPLAY = display_names.get('user')
    MAP_DISPLAY = display_names.get('map')
    LAYER_DISPLAY = display_names.get('layer')
    DOCUMENT_DISPLAY = display_names.get('document')

owner_rank_rules = resolve_extension('owner_rank_rules')
if not owner_rank_rules:
    owner_rank_rules = lambda: []
