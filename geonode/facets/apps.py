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

from django.apps import AppConfig

from geonode.facets.models import FacetProvider
from geonode.facets.providers.category import CategoryFacetProvider

logger = logging.getLogger(__name__)


class GeoNodeFacetsConfig(AppConfig):
    name = "geonode.facets"
    verbose_name = "GeoNode Facets endpoints"

    def ready(self):
        from geonode.urls import urlpatterns
        from . import urls

        urlpatterns += urls.urlpatterns


class FacetsRegistry:
    def __init__(self):
        self.facet_providers = None

    def _load_facets_configuration(self) -> None:
        """
        Facet loading is done lazily because some FacetProvider may need to access the DB, which may not have been
        initialized/created yet
        """
        self.facet_providers = dict()

        from geonode.facets.providers.thesaurus import create_thesaurus_providers
        from geonode.facets.providers.users import OwnerFacetProvider

        logger.info(f"Initializing Facets")

        self.register_facet_provider(CategoryFacetProvider())
        self.register_facet_provider(OwnerFacetProvider())

        # Thesaurus providers initialization should be called at startup and
        # whenever records in Thesaurus or ThesaurusLabel change
        for provider in create_thesaurus_providers():
            self.register_facet_provider(provider)

    def register_facet_provider(self, provider: FacetProvider):
        logger.info(f"Registering {provider}")
        self.facet_providers[provider.get_info()["name"]] = provider

    def get_providers(self):
        if self.facet_providers is None:
            self._load_facets_configuration()
        return self.facet_providers.values()

    def get_provider(self, name):
        if self.facet_providers is None:
            self._load_facets_configuration()
        return self.facet_providers.get(name, None)


facet_registry = FacetsRegistry()
