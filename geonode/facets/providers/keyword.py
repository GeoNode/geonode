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

from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from geonode.base.models import HierarchicalKeyword
from geonode.facets.models import FacetProvider, DEFAULT_FACET_PAGE_SIZE, FACET_TYPE_KEYWORD

logger = logging.getLogger(__name__)


class KeywordFacetProvider(FacetProvider):
    """
    Implements faceting for resource's keywords
    """

    @property
    def name(self) -> str:
        return "keyword"

    def get_info(self, lang="en", **kwargs) -> dict:
        return {
            "name": self.name,
            "filter": "filter{keywords.slug.in}",
            "label": _("Keyword"),
            "type": FACET_TYPE_KEYWORD,
        }

    def get_facet_items(
        self,
        queryset=None,
        start: int = 0,
        end: int = DEFAULT_FACET_PAGE_SIZE,
        lang="en",
        topic_contains: str = None,
        keys: set = {},
        **kwargs,
    ) -> (int, list):
        logger.debug("Retrieving facets for %s", self.name)

        filters = {"resourcebase__in": queryset}
        if topic_contains:
            filters["name__icontains"] = topic_contains

        if keys:
            logger.debug("Filtering by keys %r", keys)
            filters["slug__in"] = keys

        q = (
            HierarchicalKeyword.objects.filter(**filters)
            .values("slug", "name")
            .annotate(count=Count("resourcebase"))
            .order_by("-count")
        )

        cnt = q.count()

        logger.info("Found %d facets for %s", cnt, self.name)
        logger.debug(" ---> %s\n\n", q.query)
        logger.debug(" ---> %r\n\n", q.all())

        topics = [
            {
                "key": r["slug"],
                "label": r["name"],
                "count": r["count"],
            }
            for r in q[start:end].all()
        ]

        return cnt, topics

    def get_topics(self, keys: list, lang="en", **kwargs) -> list:
        q = HierarchicalKeyword.objects.filter(slug__in=keys).values("slug", "name")

        logger.debug(" ---> %s\n\n", q.query)
        logger.debug(" ---> %r\n\n", q.all())

        return [
            {
                "key": r["slug"],
                "label": r["name"],
            }
            for r in q.all()
        ]

    @classmethod
    def register(cls, registry, **kwargs) -> None:
        registry.register_facet_provider(KeywordFacetProvider(**kwargs))
