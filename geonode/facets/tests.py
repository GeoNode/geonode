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
import json
from tastypie.test import TestApiClient
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.test import RequestFactory
from django.urls import reverse

from geonode.base.models import (
    Thesaurus,
    ThesaurusLabel,
    ThesaurusKeyword,
    ThesaurusKeywordLabel,
    ResourceBase,
    Region,
    TopicCategory,
    HierarchicalKeyword,
    GroupProfile,
)
from geonode.facets.models import facet_registry
from geonode.facets.providers.baseinfo import FeaturedFacetProvider
from geonode.facets.providers.category import CategoryFacetProvider
from geonode.facets.providers.group import GroupFacetProvider
from geonode.facets.providers.keyword import KeywordFacetProvider
from geonode.facets.providers.region import RegionFacetProvider
from geonode.facets.views import ListFacetsView, GetFacetView
from geonode.tests.base import GeoNodeBaseTestSupport
from django.contrib.auth.models import Group

logger = logging.getLogger(__name__)


class TestFacets(GeoNodeBaseTestSupport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = get_user_model().objects.create(username="user_00")
        cls.admin = get_user_model().objects.get(username="admin")

        cls._create_thesauri()
        cls._create_regions()
        cls._create_categories()
        cls._create_keywords()
        cls._create_groups()
        cls._create_resources()
        cls.rf = RequestFactory()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    def setUp(self):
        super().setUp()

        self.api_client = TestApiClient()

        self.assertEqual(self.admin.username, "admin")
        self.assertEqual(self.admin.is_superuser, True)

    @classmethod
    def _create_thesauri(cls):
        cls.thesauri = {}
        cls.thesauri_k = {}

        for tn in range(2):
            t = Thesaurus.objects.create(identifier=f"t_{tn}", title=f"Thesaurus {tn}", order=100 + tn * 10)
            cls.thesauri[tn] = t
            for tl in (  # fmt: skip
                "en",
                "it",
            ):
                ThesaurusLabel.objects.create(thesaurus=t, lang=tl, label=f"TLabel {tn} {tl}")

            for tkn in range(10):
                tk = ThesaurusKeyword.objects.create(thesaurus=t, alt_label=f"T{tn}_K{tkn}_ALT")
                cls.thesauri_k[f"{tn}_{tkn}"] = tk
                for tkl in (  # fmt: skip
                    "en",
                    "it",
                ):
                    ThesaurusKeywordLabel.objects.create(keyword=tk, lang=tkl, label=f"T{tn}_K{tkn}_{tkl}")

    @classmethod
    def _create_regions(cls):
        cls.regions = {}

        for code, name in (  # fmt: skip
            ("R0", "Region0"),
            ("R1", "Region1"),
            ("R2", "Region2"),
        ):
            cls.regions[code] = Region.objects.create(code=code, name=name)

    @classmethod
    def _create_categories(cls):
        cls.cats = {}

        for code, name in (  # fmt: skip
            ("C0", "Cat0"),
            ("C1", "Cat1"),
            ("C2", "Cat2"),
            ("C3", "Cat3"),
        ):
            cls.cats[code] = TopicCategory.objects.create(identifier=code, description=name, gn_description=name)

    @classmethod
    def _create_groups(cls):
        cls.group_admin = Group.objects.create(name="UserAdmin")
        cls.group_common = Group.objects.create(name="UserCommon")
        cls.group_profile_admin = GroupProfile.objects.create(
            group_id=cls.group_admin, title="UserAdmin", slug="UserAdmin"
        )
        cls.group_profile_common = GroupProfile.objects.create(
            group_id=cls.group_common, title="UserCommon", slug="UserCommon"
        )

    @classmethod
    def _create_keywords(cls):
        cls.kw = {}

        for code, name in (  # fmt: skip
            ("K0", "Keyword0"),
            ("K1", "Keyword1"),
            ("K2", "Keyword2"),
            ("K3", "Keyword3"),
        ):
            cls.kw[code] = HierarchicalKeyword.objects.create(slug=code, name=name)

    @classmethod
    def _create_resources(self):
        public_perm_spec = {"users": {"AnonymousUser": ["view_resourcebase"]}, "groups": []}
        for x in range(20):
            d: ResourceBase = ResourceBase.objects.create(
                title=f"dataset_{x:02}",
                uuid=str(uuid4()),
                owner=self.user,
                abstract=f"Abstract for dataset {x:02}",
                subtype="vector",
                is_approved=True,
                is_published=True,
            )

            # These are the assigned keywords to the Resources

            # RB00 ->           T1K0      R0,R1    FEAT  K0      C0  group_admin
            # RB01 -> T0K0      T1K0      R0       FEAT    K1        group_admin
            # RB02 ->           T1K0         R1    FEAT      K2  C0  group_admin
            # RB03 -> T0K0      T1K0                     K0          group_admin
            # RB04 ->           T1K0                     K0K1    C0  group_admin
            # RB05 -> T0K0      T1K0                     K0  K2  C1  group_admin
            # RB06 ->           T1K0               FEAT              group_admin
            # RB07 -> T0K0      T1K0            R2 FEAT      K3  C3  group_common
            # RB08 ->           T1K0 T1K1    R1,R2 FEAT      K3  C3  group_common
            # RB09 -> T0K0      T1K0 T1K1       R2           K3  C3  group_common
            # RB10 ->                T1K1       R2           K3  C3
            # RB11 -> T0K0 T0K1      T1K1
            # RB12 ->                T1K1          FEAT
            # RB13 -> T0K0 T0K1              R1    FEAT
            # RB14 ->                              FEAT
            # RB15 -> T0K0 T0K1                                  C1
            # RB16 ->                                            C1
            # RB17 -> T0K0 T0K1
            # RB18 ->                              FEAT          C2
            # RB19 -> T0K0 T0K1                    FEAT          C2

            if x < 7:
                logger.debug(f"ASSIGNING GROUP {self.group_admin.name} TO RB {d}")
                d.group = self.group_admin

            if 7 <= x < 10:
                logger.debug(f"ASSIGNING GROUP {self.group_common.name} TO RB {d}")
                d.group = self.group_common

            if x % 2 == 1:
                logger.debug(f"ADDING KEYWORDS {self.thesauri_k['0_0']} to RB {d}")
                d.tkeywords.add(self.thesauri_k["0_0"])
            if x % 2 == 1 and x > 10:
                logger.debug(f"ADDING KEYWORDS {self.thesauri_k['0_1']} to RB {d}")
                d.tkeywords.add(self.thesauri_k["0_1"])
            if x < 10:
                logger.debug(f"ADDING KEYWORDS {self.thesauri_k['1_0']} to RB {d}")
                d.tkeywords.add(self.thesauri_k["1_0"])
            if 7 < x < 13:
                d.tkeywords.add(self.thesauri_k["1_1"])

            if (x % 6) in (0, 1, 2):
                d.featured = True

            for reg, idx in (  # fmt: skip
                ("R0", (0, 1)),
                ("R1", (0, 2, 8, 13)),
                ("R2", (7, 8, 9, 10)),
            ):
                if x in idx:
                    d.regions.add(self.regions[reg])

            for kw, idx in (  # fmt: skip
                ("K0", (0, 3, 4, 5)),
                ("K1", [1, 4]),
                ("K2", [2, 5]),
                ("K3", [7, 8, 9, 10]),
            ):
                if x in idx:
                    d.keywords.add(self.kw[kw])

            for cat, idx in (  # fmt: skip
                ("C0", [0, 2, 4]),
                ("C1", [5, 15, 16]),
                ("C2", [18, 19]),
                ("C3", [7, 8, 9, 10]),
            ):
                if x in idx:
                    d.category = self.cats[cat]

            d.save()
            d.set_permissions(public_perm_spec)

    @staticmethod
    def _facets_to_map(facets):
        return {f["name"]: f for f in facets}

    def test_facets_base(self):
        req = self.rf.get(reverse("list_facets"), data={"lang": "en"})
        res: JsonResponse = ListFacetsView.as_view()(req)
        obj = json.loads(res.content)
        self.assertIn("facets", obj)
        facets_list = obj["facets"]
        self.assertEqual(9, len(facets_list))
        fmap = self._facets_to_map(facets_list)
        for name in ("group", "category", "owner", "t_0", "t_1", "featured", "resourcetype", "keyword"):
            self.assertIn(name, fmap)

    def test_facets_rich(self):
        # make sure the resources are in
        c = ResourceBase.objects.count()
        self.assertEqual(20, c)

        # make sure tkeywords have been assigned by checking a sample resource
        rb = ResourceBase.objects.get(title="dataset_01")
        self.assertEqual(2, rb.tkeywords.count())

        # run the request
        req = self.rf.get(reverse("list_facets"), data={"include_topics": 1, "lang": "en"})
        res: JsonResponse = ListFacetsView.as_view()(req)
        obj = json.loads(res.content)

        facets_list = obj["facets"]
        self.assertEqual(9, len(facets_list))
        fmap = self._facets_to_map(facets_list)
        for expected in (  # fmt: skip
            {
                "name": "category",
                "topics": {
                    "total": 4,
                    "items": [
                        {"label": "Cat0", "count": 3},
                        {"label": "Cat1", "count": 3},
                        {"label": "Cat3", "count": 4},
                        {"label": "Cat2", "count": 2},
                    ],
                },
            },
            {
                "name": "keyword",
                "topics": {
                    "total": 4,
                    "items": [
                        {"label": "Keyword0", "count": 4},
                        {"label": "Keyword1", "count": 2},
                        {"label": "Keyword2", "count": 2},
                        {"label": "Keyword3", "count": 4},
                    ],
                },
            },
            {
                "name": "owner",
                "topics": {
                    "total": 1,
                },
            },
            {
                "name": "t_0",
                "topics": {
                    "total": 2,
                    "items": [
                        {"label": "T0_K0_en", "count": 10},
                        {"label": "T0_K1_en", "count": 5},
                    ],
                },
            },
            {
                "name": "t_1",
                "topics": {
                    "total": 2,
                    "items": [
                        {"label": "T1_K0_en", "count": 10},
                    ],
                },
            },
            {
                "name": "region",
                "topics": {
                    "total": 3,
                    "items": [
                        {"label": "Region0", "key": "R0", "count": 2},
                        {"label": "Region1", "key": "R1", "count": 4},
                        {"label": "Region2", "key": "R2", "count": 4},
                    ],
                },
            },
            {
                "name": "featured",
                "topics": {
                    "total": 2,
                    "items": [
                        {"label": "True", "key": True, "count": 11},
                        {"label": "False", "key": False, "count": 9},
                    ],
                },
            },
            {
                "name": "resourcetype",
                "topics": {
                    "total": 1,
                    "items": [
                        {"label": "resourcebase", "key": "resourcebase", "count": 20},
                    ],
                },
            },
        ):
            name = expected["name"]
            self.assertIn(name, fmap)
            facet = fmap[name]
            expected_topics = expected["topics"]
            for topic_key in expected_topics:
                if topic_key != "items":
                    self.assertEqual(
                        expected_topics[topic_key], facet["topics"][topic_key], f"Mismatching '{topic_key}' for {name}"
                    )
                else:
                    items = facet["topics"]["items"]
                    expected_items = expected_topics["items"]
                    for exp_item in expected_items:
                        exp_label = exp_item["label"]
                        found = None
                        for item in items:
                            if item["label"] == exp_label:
                                found = item
                                break

                        self.assertIsNotNone(
                            found, f"topic not found '{exp_label}' for facet '{name}' -- found items {items}"
                        )
                        for exp_field in exp_item:
                            self.assertEqual(
                                exp_item[exp_field], found[exp_field], f"Mismatch item key:{exp_field} facet:{name}"
                            )

    def test_bad_lang(self):
        # for thesauri, make sure that by requesting a non-existent language the faceting is still working,
        # using the default labels

        # run the request with a valid language
        req = self.rf.get(reverse("get_facet", args=["t_0"]), data={"lang": "en"})
        res: JsonResponse = GetFacetView.as_view()(req, "t_0")
        obj = json.loads(res.content)

        self.assertEqual(2, obj["topics"]["total"])
        self.assertEqual(10, obj["topics"]["items"][0]["count"])
        self.assertEqual("T0_K0_en", obj["topics"]["items"][0]["label"])
        self.assertTrue(obj["topics"]["items"][0]["is_localized"])

        # run the request with an INVALID language
        req = self.rf.get(reverse("get_facet", args=["t_0"]), data={"lang": "ZZ"})
        res: JsonResponse = GetFacetView.as_view()(req, "t_0")
        obj = json.loads(res.content)

        self.assertEqual(2, obj["topics"]["total"])
        self.assertEqual(10, obj["topics"]["items"][0]["count"])  # make sure the count is still there
        self.assertEqual("T0_K0_ALT", obj["topics"]["items"][0]["label"])  # check for the alternate label
        self.assertFalse(obj["topics"]["items"][0]["is_localized"])  # check for the localization flag

    def test_prefiltering(self):
        reginfo = RegionFacetProvider().get_info()
        regfilter = reginfo["filter"]
        t0filter = facet_registry.get_provider("t_0").get_info()["filter"]
        t1filter = facet_registry.get_provider("t_1").get_info()["filter"]

        for facet, filters, totals, count0 in (
            ("t_0", {}, 2, 10),
            ("t_0", {regfilter: "R0"}, 1, 1),
            ("t_1", {}, 2, 10),
            ("t_1", {regfilter: "R0"}, 1, 2),
            ("t_1", {regfilter: "R1"}, 2, 3),
            (reginfo["name"], {}, 3, 4),
            (reginfo["name"], {t0filter: self.thesauri_k["0_0"].id}, 3, 2),
            (reginfo["name"], {t1filter: self.thesauri_k["1_0"].id}, 3, 3),
        ):
            req = self.rf.get(reverse("get_facet", args=[facet]), data=filters)
            res: JsonResponse = GetFacetView.as_view()(req, facet)
            obj = json.loads(res.content)
            self.assertEqual(
                totals,
                obj["topics"]["total"],
                f"Bad totals for facet '{facet} and filter {filters}\nRESPONSE: {obj}",
            )
            self.assertEqual(
                count0, obj["topics"]["items"][0]["count"], f"Bad count0 for facet '{facet}\nRESPONSE: {obj}"
            )

    def test_prefiltering_tkeywords(self):
        regname = RegionFacetProvider().name
        featname = FeaturedFacetProvider().name
        t1filter = facet_registry.get_provider("t_1").get_info()["filter"]
        tkey_1_1 = self.thesauri_k["1_1"].id

        expected_region = {"R1": 1, "R2": 3}
        expected_feat = {True: 2, False: 3}

        # Run the single requests
        for facet, params, items in (
            (regname, {t1filter: tkey_1_1}, expected_region),
            (featname, {t1filter: tkey_1_1}, expected_feat),
        ):
            req = self.rf.get(reverse("get_facet", args=[facet]), data=params)
            res: JsonResponse = GetFacetView.as_view()(req, facet)
            obj = json.loads(res.content)

            self.assertEqual(
                len(items),
                len(obj["topics"]["items"]),
                f"Bad count for items '{facet} \n PARAMS: {params} \n RESULT: {obj} \n EXPECTED: {items}",
            )
            # search item
            for item in items.keys():
                found = next((i for i in obj["topics"]["items"] if i["key"] == item), None)
                self.assertIsNotNone(found, f"Topic '{item}' not found in facet {facet} -- {obj}")
                self.assertEqual(items[item], found.get("count", None), f"Bad count for facet '{facet}:{item}")

        # Run the single request
        req = self.rf.get(reverse("list_facets"), data={"include_topics": 1, t1filter: tkey_1_1})
        res: JsonResponse = ListFacetsView.as_view()(req)
        obj = json.loads(res.content)

        facets_list = obj["facets"]
        fmap = self._facets_to_map(facets_list)

        for name, items in (  # fmt: skip
            (regname, expected_region),
            (featname, expected_feat),
        ):
            self.assertIn(name, fmap)
            facet = fmap[name]

            for item in items.keys():
                found = next((i for i in facet["topics"]["items"] if i["key"] == item), None)
                self.assertIsNotNone(found, f"Topic '{item}' not found in facet {facet} -- {facet}")
                self.assertEqual(items[item], found.get("count", None), f"Bad count for facet '{facet}:{item}")

    def test_config(self):
        for facet, type, order in (
            ("resourcetype", None, None),
            ("t_0", "select", 100),
            ("category", "select", 5),
            ("region", "select", 7),
            ("owner", "select", 8),
        ):
            req = self.rf.get(reverse("get_facet", args=[facet]), data={"include_config": True})
            res: JsonResponse = GetFacetView.as_view()(req, facet)
            obj = json.loads(res.content)
            self.assertIn("config", obj, "Config info not found in payload")
            conf = obj["config"]

            if type is None:
                self.assertNotIn("type", conf)
            else:
                self.assertEqual(type, conf["type"], "Unexpected type")

            if order is None:
                self.assertNotIn("order", conf)
            else:
                self.assertEqual(order, conf["order"], "Unexpected order")

    def test_count0(self):
        reginfo = RegionFacetProvider().get_info()
        regflt = reginfo["filter"]
        regname = reginfo["name"]

        catinfo = CategoryFacetProvider().get_info()
        catflt = catinfo["filter"]
        catname = catinfo["name"]

        kwinfo = KeywordFacetProvider().get_info()
        kwflt = kwinfo["filter"]
        kwname = kwinfo["name"]

        groupinfo = GroupFacetProvider().get_info()
        grflt = groupinfo["filter"]
        grname = groupinfo["name"]
        g_admin_id = self.group_admin.id
        g_comm_id = self.group_common.id

        t0flt = facet_registry.get_provider("t_0").get_info()["filter"]
        t1flt = facet_registry.get_provider("t_1").get_info()["filter"]

        def t(tk):
            return self.thesauri_k[tk].id

        for facet, params, items in (  # fmt: skip
            # thesauri
            ("t_1", {regflt: "R0"}, {t("1_0"): 2}),
            ("t_1", {regflt: "R0", "key": [t("1_0")]}, {t("1_0"): 2}),
            ("t_1", {regflt: "R0", t0flt: t("0_1")}, {}),
            ("t_1", {regflt: "R0", t0flt: t("0_1"), "key": [t("1_0")]}, {t("1_0"): None}),
            (
                "t_1",
                {regflt: "R0", t0flt: t("0_1"), "key": [t("1_1"), t("1_0")]},
                {t("1_0"): None, t("1_1"): None},
            ),
            ("t_1", {"key": [t("0_1")]}, {}),
            ("t_1", {t0flt: t("0_0")}, {t("1_0"): 5, t("1_1"): 2}),
            ("t_1", {t0flt: t("0_1")}, {t("1_1"): 1}),
            ("t_1", {t0flt: [t("0_1"), t("0_0")]}, {t("1_0"): 5, t("1_1"): 2}),
            ("t_1", {catflt: ["C0"]}, {t("1_0"): 3}),
            ("t_1", {catflt: ["C0", "C1"]}, {t("1_0"): 4}),
            # regions
            (regname, {t1flt: t("1_0")}, {"R0": 2, "R1": 3, "R2": 3}),
            (regname, {t1flt: t("1_1")}, {"R1": 1, "R2": 3}),
            (regname, {t1flt: [t("1_1"), t("1_0")]}, {"R0": 2, "R1": 3, "R2": 4}),
            (regname, {t1flt: t("1_1"), "key": ["R0", "R1"]}, {"R1": 1, "R0": None}),
            (regname, {t1flt: t("1_1"), "key": ["R0"]}, {"R0": None}),
            # groups
            (grname, {grflt: [g_admin_id, g_comm_id], "key": [g_admin_id, g_comm_id]}, {g_admin_id: 7, g_comm_id: 3}),
            (grname, {grflt: [g_admin_id], "key": [g_admin_id]}, {g_admin_id: 7}),
            (grname, {catflt: ["C0"], grflt: [g_comm_id]}, {}),
            (grname, {catflt: ["C1"], grflt: [g_admin_id]}, {g_admin_id: 1}),
            (grname, {catflt: ["C0"], grflt: [g_admin_id]}, {g_admin_id: 3}),
            (grname, {catflt: ["C0", "C1"], grflt: [g_admin_id, g_comm_id]}, {g_admin_id: 4}),
            # category
            (catname, {t1flt: t("1_0")}, {"C0": 3, "C1": 1, "C3": 3}),
            (catname, {t1flt: t("1_0"), "key": ["C0", "C2"]}, {"C0": 3, "C2": None}),
            (catname, {t1flt: [t("1_0"), t("1_1")]}, {"C0": 3, "C1": 1, "C3": 4}),
            (catname, {kwflt: "K1"}, {"C0": 1}),
            (catname, {kwflt: "K1", "key": ["C0", "C2"]}, {"C0": 1, "C2": None}),
            # keyword
            (kwname, {t0flt: t("0_0")}, {"K0": 2, "K1": 1, "K2": 1, "K3": 2}),
            (kwname, {t0flt: t("1_0")}, {"K0": 4, "K1": 2, "K2": 2, "K3": 3}),
            (kwname, {t0flt: [t("1_0"), t("1_1")]}, {"K0": 4, "K1": 2, "K2": 2, "K3": 4}),
            (kwname, {t0flt: t("0_0"), regflt: "R0"}, {"K1": 1}),
            (kwname, {t0flt: t("0_0"), regflt: "R0", "key": ["K0"]}, {"K0": None}),
        ):
            req = self.rf.get(reverse("get_facet", args=[facet]), data=params)
            req.user = self.admin
            res: JsonResponse = GetFacetView.as_view()(req, facet)
            obj = json.loads(res.content)
            # self.assertEqual(totals, obj["topics"]["total"], f"Bad totals for facet '{facet} and params {params}")

            self.assertEqual(
                len(items),
                len(obj["topics"]["items"]),
                f"Bad count for items '{facet} \n PARAMS: {params} \n RESULT: {obj} \n EXPECTED: {items}",
            )
            # search item
            for item in items.keys():
                found = next((i for i in obj["topics"]["items"] if i["key"] == item), None)
                self.assertIsNotNone(found, f"Topic '{item}' not found in facet {facet} -- {obj}")
                self.assertEqual(items[item], found.get("count", None), f"Bad count for facet '{facet}:{item}")

    def test_user_auth(self):
        # make sure the user authorization pre-filters the visible resources
        # TODO test
        pass

    def test_thesauri_reloading(self):
        # Thesauri facets are cached.
        # Make sure that when Thesauri or ThesauriLabel change the facets cache is invalidated
        # TODO impl+test

        pass

    def test_group_facet_api_call(self):
        resource_count_admin = 7
        resource_count_common = 3

        expected_response_base = {
            "name": "group",
            "filter": "filter{group.in}",
            "label": "Group",
            "type": "group",
            "topics": {
                "page": 0,
                "page_size": 10,
                "start": 0,
                "total": 2,
                "items": [
                    {
                        "key": self.group_profile_admin.group_id,
                        "label": self.group_profile_admin.slug,
                        "count": resource_count_admin,
                    },
                    {
                        "key": self.group_profile_common.group_id,
                        "label": self.group_profile_common.slug,
                        "count": resource_count_common,
                    },
                ],
            },
        }
        expected_response_filtered = {
            "name": "group",
            "filter": "filter{group.in}",
            "label": "Group",
            "type": "group",
            "topics": {
                "page": 0,
                "page_size": 10,
                "start": 0,
                "total": 1,
                "items": [
                    {
                        "key": self.group_profile_admin.group_id,
                        "label": self.group_profile_admin.slug,
                        "count": resource_count_admin,
                    }
                ],
            },
        }

        url_filtered = f"{reverse('get_facet',args=['group'])}?filter{{group.in}}={self.group_admin.id}&include_topics=true&key={self.group_admin.id}"
        url_base = f"{reverse('get_facet',args=['group'])}"

        response_filtered = self.client.get(url_filtered)
        response_dict_filtered = response_filtered.json()

        response_base = self.client.get(url_base)
        response_dict_base = response_base.json()

        self.assertEqual(
            response_filtered.status_code,
            200,
            "Unexpected status code, got %s expected 200" % (response_filtered.status_code),
        )
        self.assertEqual(
            response_base.status_code, 200, "Unexpected status code, got %s expected 200" % (response_base.status_code)
        )

        self.assertDictEqual(expected_response_filtered, response_dict_filtered)
        self.assertDictEqual(expected_response_base, response_dict_base)

    def test_group_facets_are_filtered_by_words(self):
        # there are some groups and the facets return them
        url = f"{reverse('get_facet',args=['group'])}"

        response = self.client.get(url)
        self.assertEqual(200, response.status_code, response.json())

        self.assertTrue(response.json().get("topics", {}).get("total", 0) > 0)

        # topic_contains with real name should return 1
        url = f"{reverse('get_facet',args=['group'])}?topic_contains=UserAdmin"
        response = self.client.get(url)

        self.assertEqual(200, response.status_code, response.json())

        self.assertEqual(1, response.json().get("topics", {}).get("total", 0))

        # topic_contains with a random string to be searched for should be 0
        url = f"{reverse('get_facet',args=['group'])}?topic_contains=abc123scfuqbrwefbasascgiu"
        response = self.client.get(url)

        self.assertEqual(200, response.status_code, response.json())

        self.assertEqual(0, response.json().get("topics", {}).get("total", 0))
