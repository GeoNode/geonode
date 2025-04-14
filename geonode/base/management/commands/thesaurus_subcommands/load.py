#########################################################################
#
# Copyright (C) 2016 OSGeo
# Copyright (C) 2022 King's College London
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

from os import path
from typing import List

from rdflib import Graph, Literal
from rdflib.namespace import RDF, RDFS, SKOS, DC, DCTERMS
from rdflib.util import guess_format

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.core.management.base import CommandError
from django.db import models

from geonode.base.management.command_utils import setup_logger
from geonode.base.models import Thesaurus, ThesaurusKeyword, ThesaurusKeywordLabel, ThesaurusLabel

logger = setup_logger()

ACTION_CREATE = "create"
ACTION_UPDATE = "update"
ACTION_APPEND = "append"
ACTION_PARSE = "parse"

ACTIONS = [ACTION_CREATE, ACTION_UPDATE, ACTION_APPEND, ACTION_PARSE]

FAKE_BASE_URI = "http://automatically/added/uri/"


def load_thesaurus(input_file, identifier: str, action: str = ACTION_CREATE):
    g = Graph()

    # if the input_file is an UploadedFile object rather than a file path the Graph.parse()
    # method may not have enough info to correctly guess the type; in this case supply the
    # name, which should include the extension, to guess_format manually...

    filename = input_file.name if isinstance(input_file, UploadedFile) else input_file
    rdf_format = guess_format(filename)
    if not identifier:
        identifier, _ = path.splitext(path.basename(filename))
        logger.info(f"Missing identifier param: Inferring thesaurus identifier as '{identifier}'")

    g.parse(input_file, format=rdf_format, publicID=FAKE_BASE_URI)

    # An error will be thrown here there is more than one scheme in the file
    scheme = g.value(None, RDF.type, SKOS.ConceptScheme, any=False)
    if scheme is None:
        raise CommandError("ConceptScheme not found in file")

    default_lang = getattr(settings, "THESAURUS_DEFAULT_LANG", None)

    available_titles = [t for t in g.objects(scheme, DC.title) if isinstance(t, Literal)]
    thesaurus_title = value_for_language(available_titles, default_lang)
    description = g.value(scheme, DC.description, None, default=thesaurus_title)
    date_issued = g.value(scheme, DCTERMS.issued, None, default="")

    logger.info(f'Thesaurus parsed: Title: "{thesaurus_title}", desc: "{description}" issued at {date_issued}')

    thesaurus, cr_t = _run_action(
        action,
        Thesaurus,
        {"identifier": identifier},
        {"date": date_issued, "description": description, "title": thesaurus_title, "about": str(scheme)},
        {},
    )

    tl_cnt = tl_add = 0
    tk_cnt = tk_add = 0
    tkl_cnt = tkl_add = 0

    for lang in available_titles:
        if lang.language is not None:
            thesaurus_label, c = _run_action(
                action,
                ThesaurusLabel,
                {
                    "thesaurus": thesaurus,
                    "lang": lang.language,
                },
                {"label": lang.value},
                {},
            )
            tl_cnt += 1
            tl_add += 1 if c else 0

    for concept in g.subjects(RDF.type, SKOS.Concept):
        prefs = preferredLabel(g, concept, default_lang)
        pref = prefs[0][1] if prefs else "-"
        about = str(concept)
        about = about.removeprefix(FAKE_BASE_URI) if about.startswith(FAKE_BASE_URI) else about
        alt_label = g.value(concept, SKOS.altLabel, object=None, default=None)
        if alt_label is not None:
            alt_label = str(alt_label)
        else:
            available_labels = [t for t in g.objects(concept, SKOS.prefLabel) if isinstance(t, Literal)]
            alt_label = value_for_language(available_labels, default_lang)

        logger.info(f" - Parsed Concept -> about:'{about}' alt:'{alt_label}' pref:'{str(pref)}' ")

        tk, c = _run_action(
            action,
            ThesaurusKeyword,
            {
                "thesaurus": thesaurus,
                "about": about,
            },
            {"alt_label": alt_label},
            {},
        )
        tk_cnt += 1
        tk_add += 1 if c else 0

        for _, pref_label in preferredLabel(g, concept):
            lang = pref_label.language
            label = str(pref_label)
            logger.info(f"   - Label {lang}: {label}")

            tkl, c = _run_action(
                action,
                ThesaurusKeywordLabel,
                {
                    "keyword": tk,
                    "lang": lang,
                },
                {"label": label},
                {},
            )
            tkl_cnt += 1
            tkl_add += 1 if c else 0

    logger.warning(f"Thesaurus added:                {cr_t}")
    logger.warning(f"ThesaurusLabel added:         {tl_add:3}/{tl_cnt:3}")
    logger.warning(f"ThesaurusKeyword added:       {tk_add:3}/{tk_cnt:3}")
    logger.warning(f"ThesaurusKeywordLabel added:  {tkl_add:3}/{tkl_cnt:3}")


def _run_action(action: str, model: type[models.Model], pk_dict, upd_dict, create_dict) -> tuple[models.Model, bool]:
    def update_or_create(defaults=upd_dict, create_defaults=create_dict, **pk_dict):
        # this signature is available since django 5
        obj, created = model.objects.get_or_create(defaults=upd_dict | create_dict, **pk_dict)

        if not created:
            rows = model.objects.filter(pk=obj.pk).update(**upd_dict)
            if rows != 1:
                logger.error(f"UPDATED {rows} rows for {model.__name__} -> {pk_dict}")

        return obj, created

    if action in (ACTION_CREATE, ACTION_PARSE):
        obj = model(**(pk_dict | upd_dict | create_dict))
        created = False
        if action == ACTION_CREATE:
            obj.save()
            created = True

    elif action == ACTION_UPDATE:
        obj, created = update_or_create(defaults=upd_dict, create_defaults=create_dict, **pk_dict)
        if created:
            logger.info(f"{model.__name__} -> Created id:{pk_dict}")
        else:
            logger.info(f"{model.__name__} -> Updated id:{pk_dict} DATA:{upd_dict}")

    elif action == ACTION_APPEND:
        obj, created = model.objects.get_or_create(defaults=upd_dict | create_dict, **pk_dict)
        if created:
            logger.info(f"{model.__name__} -> Created {pk_dict}")
    else:
        raise CommandError("No valid action found")

    return obj, created


def create_fake_thesaurus(name):
    thesaurus = Thesaurus()
    thesaurus.identifier = name

    thesaurus.title = f"Title: {name}"
    thesaurus.description = "SAMPLE FAKE THESAURUS USED FOR TESTING"
    thesaurus.date = "2016-10-01"

    thesaurus.save()

    for keyword in ["aaa", "bbb", "ccc"]:
        tk = ThesaurusKeyword()
        tk.thesaurus = thesaurus
        tk.about = f"{keyword}_about"
        tk.alt_label = f"{keyword}_alt"
        tk.save()

        for _l in ["it", "en", "es"]:
            tkl = ThesaurusKeywordLabel()
            tkl.keyword = tk
            tkl.lang = _l
            tkl.label = f"{keyword}_l_{_l}_t_{name}"
            tkl.save()


def value_for_language(available: List[Literal], default_lang: str) -> str:
    sorted_lang = sorted(available, key=lambda literal: "" if literal.language is None else literal.language)
    for item in sorted_lang:
        if item.language is None:
            return str(item)
        elif item.language.split("-")[0] == default_lang:
            return str(item)
    return str(available[0])


def preferredLabel(
    g,
    subject,
    lang=None,
    default=None,
    label_properties=(SKOS.prefLabel, RDFS.label),
):
    """
    Find the preferred label for subject.

    By default prefers skos:prefLabels over rdfs:labels. In case at least
    one prefLabel is found returns those, else returns labels. In case a
    language string (e.g., "en", "de" or even "" for no lang-tagged
    literals) is given, only such labels will be considered.

    Return a list of (labelProp, label) pairs, where labelProp is either
    skos:prefLabel or rdfs:label.

    Copied from rdflib 6.1.1
    """

    if default is None:
        default = []

    # setup the language filtering
    if lang is not None:
        if lang == "":  # we only want not language-tagged literals

            def langfilter(l_):
                return l_.language is None

        else:

            def langfilter(l_):
                return l_.language == lang

    else:  # we don't care about language tags

        def langfilter(l_):
            return True

    for labelProp in label_properties:
        labels = list(filter(langfilter, g.objects(subject, labelProp)))
        if len(labels) == 0:
            continue
        else:
            return [(labelProp, l_) for l_ in labels]
    return default
