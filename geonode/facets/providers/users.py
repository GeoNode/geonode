import logging

from django.db.models import Count

from geonode.facets.models import FacetProvider, DEFAULT_FACET_PAGE_SIZE, FACET_TYPE_USER

logger = logging.getLogger(__name__)


class OwnerFacetProvider(FacetProvider):
    """
    Implements faceting for users owner of the resources
    """

    @property
    def name(self) -> str:
        return "owner"

    def get_info(self, lang="en") -> dict:
        return {
            "name": "owner",
            "key": "owner",
            "label": "Owner",
            "type": FACET_TYPE_USER,
            "hierarchical": False,
            "order": 5,
        }

    def get_facet_items(
        self,
        queryset=None,
        start: int = 0,
        end: int = DEFAULT_FACET_PAGE_SIZE,
        lang="en",
        topic_contains: str = None,
    ) -> (int, list):
        logger.debug("Retrieving facets for OWNER")

        q = queryset.values("owner", "owner__username")
        if topic_contains:
            q = q.filter(owner__username__icontains=topic_contains)
        q = q.annotate(count=Count("owner")).order_by("-count")

        cnt = q.count()

        logger.info("Found %d facets for %s", cnt, self.name)
        logger.debug(" ---> %s\n\n", q.query)
        logger.debug(" ---> %r\n\n", q.all())

        topics = [
            {
                "key": r["owner"],
                "label": r["owner__username"],
                "localized_label": r["owner__username"],
                "count": r["count"],
            }
            for r in q[start:end].all()
        ]

        return cnt, topics

    @classmethod
    def register(cls, registry, **kwargs) -> None:
        registry.register_facet_provider(OwnerFacetProvider())
