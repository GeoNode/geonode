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

from django.db.models import Count, OuterRef, Subquery

from geonode.base.models import ThesaurusKeyword, ThesaurusKeywordLabel
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
        }

        if topic_contains:
            filter["tkeywords__keyword__label__icontains"] = topic_contains

        q = (
            queryset.filter(**filter)
            .values("tkeywords", "tkeywords__alt_label")
            .annotate(count=Count("tkeywords"))
            .annotate(
                localized_label=Subquery(
                    ThesaurusKeywordLabel.objects.filter(keyword=OuterRef("tkeywords"), lang=lang).values("label")
                )
            )
            .order_by("-count")
        )

        logger.debug(" ---> %s\n\n", q.query)

        cnt = q.count()

        logger.info("Found %d facets for %s", cnt, self._name)
        logger.debug(" ---> %r\n\n", q.all())

        topics = [
            {
                "key": r["tkeywords"],
                "label": r["localized_label"] or r["tkeywords__alt_label"],
                "is_localized": r["localized_label"] is not None,
                "count": r["count"],
            }
            for r in q[start:end].all()
        ]

        return cnt, topics

    def get_topics(self, keys: list, lang="en", **kwargs) -> list:
        q = (
            ThesaurusKeyword.objects.filter(id__in=keys)
            .values("id", "alt_label")
            .annotate(
                localized_label=Subquery(
                    ThesaurusKeywordLabel.objects.filter(keyword=OuterRef("id"), lang=lang).values("label")
                )
            )
        )

        logger.debug(" ---> %s\n\n", q.query)
        logger.debug(" ---> %r\n\n", q.all())

        return [
            {
                "key": r["id"],
                "label": r["localized_label"] or r["alt_label"],
                "is_localized": r["localized_label"] is not None,
            }
            for r in q.all()
        ]

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
