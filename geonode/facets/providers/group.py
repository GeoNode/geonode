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
from django.db.models import Count

from geonode.facets.models import FacetProvider, DEFAULT_FACET_PAGE_SIZE, FACET_TYPE_GROUP
from geonode.groups.models import GroupProfile
from geonode.security.utils import get_user_visible_groups

logger = logging.getLogger(__name__)


class GroupFacetProvider(FacetProvider):
    """
    Implements faceting for resource's group
    """

    @property
    def name(self) -> str:
        return "group"

    def get_info(self, lang="en", **kwargs) -> dict:
        return {
            "name": self.name,
            "filter": "filter{group.in}",
            "label": _("Group"),
            "type": FACET_TYPE_GROUP,
        }

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
        logger.debug("Retrieving facets for %s", self.name)

        filters = dict()
        if keys:
            logger.debug("Filtering by keys %r", keys)
            filters["group__id__in"] = keys

        if topic_contains:
            filters["group__name__icontains"] = topic_contains

        visible_groups = get_user_visible_groups(user=kwargs["user"])

        q = (
            queryset.values("group__name", "group__id")
            .annotate(count=Count("group__id"))
            .filter(**filters)
            .filter(group__id__in=[group.group_id for group in visible_groups])
            .order_by("-count")
        )

        logger.debug(" PREFILTERED QUERY  ---> %s\n\n", queryset.query)
        logger.debug(" ADDITIONAL FILTERS ---> %s\n\n", filters)
        logger.debug(" FINAL QUERY        ---> %s\n\n", q.query)

        cnt = q.count()
        logger.debug(f" q.count()  {q.count()}")
        logger.info("Found %d facets for %s", cnt, self.name)
        logger.debug(" ---> %s\n\n", q.query)
        logger.debug(" ---> %r\n\n", q.all())

        topics = [
            {
                "key": r["group__id"],
                "label": r["group__name"],
                "count": r["count"],
            }
            for r in q[start:end].all()
        ]

        return cnt, topics

    def get_topics(self, keys: list, lang="en", **kwargs) -> list:
        q = GroupProfile.objects.filter(group__id__in=keys)

        logger.debug(" ---> %s\n\n", q.query)
        logger.debug(" ---> %r\n\n", q.all())

        return [{"key": r.group_id, "label": r.slug, "count": len(list(r.resources()))} for r in q.all()]

    @classmethod
    def register(cls, registry, **kwargs) -> None:
        registry.register_facet_provider(GroupFacetProvider(**kwargs))
