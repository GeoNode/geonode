import logging

from django.db.models import Count

from geonode.facets.models import FacetProvider, DEFAULT_FACET_PAGE_SIZE, FACET_TYPE_THESAURUS

logger = logging.getLogger(__name__)


class ThesaurusFacetProvider(FacetProvider):
    """
    Implements faceting for a given Thesaurus
    """

    def __init__(self, identifier, title, order, labels: dict):
        self._name = identifier
        self.label = title
        self.order = order
        self.labels = labels

    @property
    def name(self) -> str:
        return self._name

    def get_info(self, lang="en") -> dict:
        return {
            "name": self._name,
            "key": "filter{tkeywords}",
            "label": self.labels.get(lang, self.label),
            "is_localized": self.labels.get(lang, None) is not None,
            "type": FACET_TYPE_THESAURUS,
            "hierarchical": False,
            "order": self.order,
        }

    def get_facet_items(
        self,
        queryset=None,
        start: int = 0,
        end: int = DEFAULT_FACET_PAGE_SIZE,
        lang="en",
        topic_contains: str = None,
        **kwargs,
    ) -> (int, list):
        logger.debug("Retrieving facets for %s", self._name)

        filter = {
            "tkeywords__thesaurus__identifier": self._name,
            "tkeywords__keyword__lang": lang,
        }

        if topic_contains:
            filter["tkeywords__keyword__label__icontains"] = topic_contains

        q = (
            queryset.filter(**filter)
            .values("tkeywords", "tkeywords__keyword__label", "tkeywords__alt_label")
            .annotate(count=Count("tkeywords"))
            .order_by("-count")
        )

        cnt = q.count()

        logger.info("Found %d facets for %s", cnt, self._name)
        logger.debug(" ---> %s\n\n", q.query)
        logger.debug(" ---> %r\n\n", q.all())

        topics = [
            {
                "key": r["tkeywords"],
                "label": r["tkeywords__keyword__label"] or r["tkeywords__alt_label"],
                "is_localized": r["tkeywords__keyword__label"] is not None,
                "count": r["count"],
            }
            for r in q[start:end].all()
        ]

        return cnt, topics

    @classmethod
    def register(cls, registry, **kwargs) -> None:
        # registry.register_facet_provider(CategoryFacetProvider())
        from geonode.base.models import Thesaurus

        # this query return the list of thesaurus X the list of localized titles
        q = (
            Thesaurus.objects.filter(facet=True)
            .values("identifier", "title", "order", "rel_thesaurus__label", "rel_thesaurus__lang")
            .order_by("order")
        )

        # coalesce the localized labels
        ret = {}
        for r in q.all():
            identifier = r["identifier"]
            t = ret.get(identifier, None)
            if not t:
                t = {k: r[k] for k in ("identifier", "title", "order")}
                t["labels"] = {}
            if r["rel_thesaurus__lang"] and r["rel_thesaurus__label"]:
                t["labels"][r["rel_thesaurus__lang"]] = r["rel_thesaurus__label"]
            ret[identifier] = t

        logger.info("Creating providers for %r", ret)
        for t in ret.values():
            registry.register_facet_provider(
                ThesaurusFacetProvider(t["identifier"], t["title"], t["order"], t["labels"])
            )
