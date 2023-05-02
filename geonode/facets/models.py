DEFAULT_FACET_TOPICS_LIMIT = 10


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
        - 'label': a possibly localized label for this provider (localized according to the `lang` param
        - 'type': the facet type (e.g. user, region, thesaurus, ...)
        - 'hierarchical': boolean value telling if the facet items are hierarchically organized
        - "order": an optional integer suggesting the relative ordering of the facets

        :param lang: lanuage for label localization
        :return: a dict
        """
        pass

    def get_facet_items(self, queryset=None, lang="en", page: int = 0, limit: int = DEFAULT_FACET_TOPICS_LIMIT):
        """
        Return the items of the facets, as a dict:
        - total: int, number of items matched
        - start: int: the index of the initial returned items
        - page: int: the returned page (should be the same as the `page` param)
        - limit: int: the page size  (should be the same as the `limit` param)
        - items: list of topic record. A topic record is a dict having these keys:
          - key: the key of the items that should be used for filtering
          - label: a possibly localized label for the item
          - count: the count of such topic in the current facet
        :param queryset: the prefiltered queryset (may be filtered for authorization or other filters)
        :param lang: the preferred language for the labels
        :param page: page pagination param
        :param limit: limit pagination param
        :return: a dict
        """
        pass
