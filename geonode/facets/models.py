#########################################################################
#
# Copyright (C) 2023 Open Source Geospatial Foundation - all rights reserved
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

from django.conf import settings

DEFAULT_FACET_PAGE_SIZE = 10

# Well known types of facet - not an enum bc it needs to be extensible
FACET_TYPE_PLACE = "place"
FACET_TYPE_USER = "user"
FACET_TYPE_THESAURUS = "thesaurus"
FACET_TYPE_CATEGORY = "category"
FACET_TYPE_BASE = "base"
FACET_TYPE_KEYWORD = "keyword"
FACET_TYPE_GROUP = "group"

logger = logging.getLogger(__name__)


class FacetProvider:
    """
    Provides access to the facet information and the related topics
    """

    def __init__(self, **kwargs):
        self.config = kwargs.get("config", {}).copy()

    def __str__(self):
        return f"{self.__class__.__name__}[{self.name}]"

    @property
    def name(self) -> str:
        """
        Get the name of the facet, to be used as a key for this provider.
        You may want to override this method in order to have an optimized logic
        :return: The name of the provider as a str
        """
        self.get_info()["name"]

    def get_info(self, lang="en", **kwargs) -> dict:
        """
        Get the basic info for this provider, as a dict with these keys:
        - 'name': the name of the provider (the one returned by name())
        - 'filter': the filtering key to be used in a filter query
        - 'label': a generic label for the facet; the client should try and localize it whenever possible
        - 'localized_label': a localized label for the facet (localized according to the `lang` param)
        - 'type': the facet type (e.g. user, region, thesaurus, ...)
        - 'hierarchical': boolean value telling if the facet items are hierarchically organized
        - "order": an optional integer suggesting the relative ordering of the facets

        :param lang: lanuage for label localization
        :return: a dict
        """
        pass

    def get_facet_items(
        self,
        queryset,
        start: int = 0,
        end: int = DEFAULT_FACET_PAGE_SIZE,
        lang="en",
        topic_contains: str = None,
        keys: set = {},
        **kwargs,
    ) -> (int, list):
        """
        Return the items of the facets, in a tuple:
        - int, total number of items matched
        - list, topic records. A topic record is a dict having these keys:
          - key: the key of the items that should be used for filtering
          - label: a generic label for the item; the client should try and localize it whenever possible
          - localized_label: a localized label for the item
          - count: the count of such topic in the current facet
          - other facet specific keys
        :param queryset: the prefiltered queryset (may be filtered for authorization or other filters)
        :param start: int: pagination, the index of the initial returned item
        :param end: int: pagination, the index of the last returned item
        :param lang: the preferred language for the labels
        :param topic_contains: only returns matching topics
        :param keys: only returns topics with given keys, even if their count is 0
        :return: a tuple int:total count of record, list of items
        """
        pass

    def get_topics(self, keys: list, lang="en", **kwargs) -> list:
        """
        Return the topics with the requested ids as a list
        - list, topic records. A topic record is a dict having these keys:
          - key: the key of the items that should be used for filtering
          - label: a generic label for the item; the client should try and localize it whenever possible
          - localized_label: a localized label for the item
          - other facet specific keys
        :param keys: the list of the keys of the topics, as returned by the get_facet_items() method
        :param lang: the preferred language for the labels
        :return: list of items
        """
        pass

    @classmethod
    def register(cls, registry, **kwargs) -> None:
        """
        Perform registration of instances of this Provider
        :param registry: the registry where instances shall be registered
        :param kwargs: other args that may be needed by Providers
        """
        pass


class FacetsRegistry:
    def __init__(self):
        self.facet_providers = None

    def _load_facets_configuration(self) -> None:
        """
        Facet loading is done lazily because some FacetProvider may need to access the DB, which may not have been
        initialized/created yet
        """
        from django.utils.module_loading import import_string

        self.facet_providers = dict()

        logger.info("Initializing Facets")

        for providerconf in getattr(settings, "FACET_PROVIDERS", []):
            clz = providerconf["class"]
            provider = import_string(clz)
            provider.register(self, config=providerconf.get("config", {}))

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
