DEFAULT_FACET_PAGE_SIZE = 10


class FacetProvider:
    """
    Provides access to the facet information and the related topics
    """

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

    def get_info(self, lang="en") -> dict:
        """
        Get the basic info for this provider, as a dict with these keys:
        - 'name': the name of the provider (the one returned by name())
        - 'key': the filtering key to be used in a filter query
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
        self, queryset, start: int = 0, end: int = DEFAULT_FACET_PAGE_SIZE, lang="en", topic_contains: str = None
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
        :return: a tuple int:total count of record, list of items
        """
        pass
