import logging

from django.db.models import Count

from geonode.base.models import Thesaurus
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
            "key": "filter{tkeyword}",
            "label": self.label,
            "localized_label": self.labels.get(lang, None),
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
                "localized_label": r["tkeywords__keyword__label"],
                "label": r["tkeywords__alt_label"],
                "count": r["count"],
            }
            for r in q[start:end].all()
        ]

        return cnt, topics


def create_thesaurus_providers() -> list:
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

    logging.info("Creating providers for %r", ret)
    return [ThesaurusFacetProvider(t["identifier"], t["title"], t["order"], t["labels"]) for t in ret.values()]
