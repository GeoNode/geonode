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

from geonode.facets.models import FacetProvider, DEFAULT_FACET_PAGE_SIZE, FACET_TYPE_BASE

logger = logging.getLogger(__name__)


class ResourceTypeFacetProvider(FacetProvider):
    """
    Implements faceting for resources' type and subtype
    """

    @property
    def name(self) -> str:
        return "resourcetype"

    def get_info(self, lang="en", **kwargs) -> dict:
        return {
            "name": self.name,
            "filter": "filter{resource_type.in}",
            "label": "Resource type",
            "type": FACET_TYPE_BASE,
            "hierarchical": True,
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

        if topic_contains:
            logger.warning(f"Facet {self.name} does not support topic_contains filtering")

        q = queryset.values("resource_type", "subtype")
        q = q.annotate(ctype=Count("resource_type"), csub=Count("subtype"))
        q = q.order_by()

        # aggregate subtypes into rtypes
        tree = {}
        for r in q.all():
            res_type = r["resource_type"]
            t = tree.get(res_type, {"cnt": 0, "sub": {}})
            t["cnt"] += r["ctype"]
            if sub := r["subtype"]:
                t["sub"][sub] = {"cnt": r["ctype"]}
            tree[res_type] = t

        logger.info("Found %d main facets for %s", len(tree), self.name)
        logger.debug(" ---> %s\n\n", q.query)
        logger.debug(" ---> %r\n\n", q.all())

        topics = []
        for rtype, info in tree.items():
            t = {"key": rtype, "label": rtype, "count": info["cnt"]}
            if sub := info["sub"]:
                children = []
                for stype, sinfo in sub.items():
                    children.append({"key": stype, "label": stype, "count": sinfo["cnt"]})
                t["filter"] = "filter{subtype.in}"
                t["items"] = sorted(children, reverse=True, key=lambda x: x["count"])
            topics.append(t)

        return len(topics), sorted(topics, reverse=True, key=lambda x: x["count"])

    @classmethod
    def register(cls, registry, **kwargs) -> None:
        registry.register_facet_provider(ResourceTypeFacetProvider(**kwargs))


class FeaturedFacetProvider(FacetProvider):
    """
    Implements faceting for resources flagged as featured
    """

    @property
    def name(self) -> str:
        return "featured"

    def get_info(self, lang="en", **kwargs) -> dict:
        return {
            "name": self.name,
            "filter": "filter{featured}",
            "label": "Featured",
            "type": FACET_TYPE_BASE,
            "hierarchical": False,
            "order": 0,
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

        if topic_contains:
            logger.warning(f"Facet {self.name} does not support topic_contains filtering")

        q = queryset.values("featured").annotate(cnt=Count("featured")).order_by()

        logger.debug(" ---> %s\n\n", q.query)
        logger.debug(" ---> %r\n\n", q.all())

        topics = [
            {
                "key": r["featured"],
                "label": str(r["featured"]),
                "count": r["cnt"],
            }
            for r in q[start:end]
        ]

        return 2, topics

    @classmethod
    def register(cls, registry, **kwargs) -> None:
        registry.register_facet_provider(FeaturedFacetProvider(**kwargs))
