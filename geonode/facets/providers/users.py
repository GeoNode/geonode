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

from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
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

    def get_info(self, lang="en", **kwargs) -> dict:
        return {
            "name": "owner",
            "filter": "filter{owner.pk.in}",
            "label": _("Owner"),
            "type": FACET_TYPE_USER,
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
        logger.debug("Retrieving facets for OWNER")

        filters = dict()

        if topic_contains:
            filters["owner__username__icontains"] = topic_contains

        if keys:
            logger.debug("Filtering by keys %r", keys)
            filters["owner__in"] = keys

        q = (
            queryset.values("owner", "owner__username")
            .filter(**filters)
            .annotate(count=Count("owner"))
            .order_by("-count")
        )

        cnt = q.count()

        logger.info("Found %d facets for %s", cnt, self.name)
        logger.debug(" ---> %s\n\n", q.query)
        logger.debug(" ---> %r\n\n", q.all())

        topics = [
            {
                "key": r["owner"],
                "label": r["owner__username"],
                "count": r["count"],
            }
            for r in q[start:end]
        ]

        return cnt, topics

    def get_topics(self, keys: list, lang="en", **kwargs) -> list:
        q = get_user_model().objects.filter(id__in=keys).values("id", "username")

        logger.debug(" ---> %s\n\n", q.query)
        logger.debug(" ---> %r\n\n", q.all())

        return [
            {
                "key": r["id"],
                "label": r["username"],
            }
            for r in q.all()
        ]

    @classmethod
    def register(cls, registry, **kwargs) -> None:
        registry.register_facet_provider(OwnerFacetProvider(**kwargs))
