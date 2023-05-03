import logging

from django.db.models import Count

from geonode.facets.models import FacetProvider, DEFAULT_FACET_PAGE_SIZE, FACET_TYPE_CATEGORY

logger = logging.getLogger(__name__)


class CategoryFacetProvider(FacetProvider):
    """
    Implements faceting for resource's topicCategory
    """

    @property
    def name(self) -> str:
        return "category"

    def get_info(self, lang="en") -> dict:
        return {
            "name": self.name,
            "key": "filter{category__identifier}",
            "label": "Category",
            "type": FACET_TYPE_CATEGORY,
            "hierarchical": False,
            "order": 2,
        }

    def get_facet_items(
        self,
        queryset=None,
        start: int = 0,
        end: int = DEFAULT_FACET_PAGE_SIZE,
        lang="en",
        topic_contains: str = None,
    ) -> (int, list):
        logger.debug("Retrieving facets for %s", self.name)

        q = queryset.values("category__identifier", "category__gn_description", "category__fa_class")
        if topic_contains:
            q = q.filter(category__gn_description=topic_contains)
        q = q.annotate(count=Count("owner")).order_by("-count")

        cnt = q.count()

        logger.info("Found %d facets for %s", cnt, self.name)
        logger.debug(" ---> %s\n\n", q.query)
        logger.debug(" ---> %r\n\n", q.all())

        topics = [
            {
                "key": r["category__identifier"],
                "label": r["category__gn_description"],
                "localized_label": r["category__gn_description"],
                "count": r["count"],
                "fa_class": r["category__fa_class"],
            }
            for r in q[start:end].all()
        ]

        return cnt, topics
