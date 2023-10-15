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

from geonode.facets.models import FacetProvider, DEFAULT_FACET_PAGE_SIZE, FACET_TYPE_PLACE

logger = logging.getLogger(__name__)


class RegionFacetProvider(FacetProvider):
    """
    Implements faceting for resource's regions
    """

    @property
    def name(self) -> str:
        return "region"

    def get_info(self, lang="en") -> dict:
        return {
            "name": self.name,
            "key": "filter{regions.code.in}",
            "label": "Region",
            "type": FACET_TYPE_PLACE,
            "hierarchical": False,  # source data is hierarchical, but this implementation is flat
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

        q = queryset.filter(regions__isnull=False).values("regions__code", "regions__name")
        if topic_contains:
            q = q.filter(regions__name=topic_contains)
        q = q.annotate(count=Count("regions__code")).order_by("-count")

        cnt = q.count()

        logger.info("Found %d facets for %s", cnt, self.name)
        logger.debug(" ---> %s\n\n", q.query)
        logger.debug(" ---> %r\n\n", q.all())

        topics = [
            {
                "key": r["regions__code"],
                "label": r["regions__name"],
                "count": r["count"],
            }
            for r in q[start:end].all()
        ]

        return cnt, topics

    @classmethod
    def register(cls, registry, **kwargs) -> None:
        registry.register_facet_provider(RegionFacetProvider())
