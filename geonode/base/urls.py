
#########################################################################
#
# Copyright (C) 2019 OSGeo
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


from django.conf.urls import url
from django.conf import settings

from .views import (
    ResourceBaseAutocomplete, RegionAutocomplete,
    HierarchicalKeywordAutocomplete, ThesaurusKeywordLabelAutocomplete, 
    EmbrapaKeywordsAutocomplete, EmbrapaUnityAutocomplete, EmbrapaPurposeAutocomplete)


urlpatterns = [
    url(
        r'^autocomplete_response/$',
        ResourceBaseAutocomplete.as_view(),
        name='autocomplete_base',
    ),

    url(
        r'^autocomplete_region/$',
        RegionAutocomplete.as_view(),
        name='autocomplete_region',
    ),

    url(
        r'^autocomplete_hierachical_keyword/$',
        HierarchicalKeywordAutocomplete.as_view(),
        name='autocomplete_hierachical_keyword',
    ),
    url(
        r'^autocomplete_embrapa_keywords/$',
        EmbrapaKeywordsAutocomplete.as_view(),
        name='autocomplete_embrapa_keywords',
    ),
    url(
        r'^autocomplete_embrapa_unity/$',
        EmbrapaUnityAutocomplete.as_view(),
        name='autocomplete_embrapa_unity',
    ),
    url(
        r'^autocomplete_embrapa_purpose/$',
        EmbrapaPurposeAutocomplete.as_view(),
        name='autocomplete_embrapa_purpose',
    ),
]

#Adicionado a url do embrapa_keywords

# Only register the url for thesuarus if it is enabled in settings
if hasattr(settings, 'THESAURUS') and settings.THESAURUS:

    urlpatterns.append(
        url(
        r'^thesaurus_autocomplete/$',
        ThesaurusKeywordLabelAutocomplete.as_view(),
        name='thesaurus_autocomplete',
        ),
    )
