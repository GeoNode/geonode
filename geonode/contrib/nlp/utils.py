# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

import os
import sys

from django.conf import settings

from taggit.models import Tag

from geonode.base.models import Region

global ner
ner = None


def _load_ner():
    global ner
    if settings.NLP_ENABLED:
        try:
            if not (settings.NLP_LIBRARY_PATH in sys.path):
                sys.path.append(settings.NLP_LIBRARY_PATH)
            if not ner:
                from mitie import named_entity_extractor
                ner = named_entity_extractor(settings.NLP_MODEL_PATH)
        except:
            print "Could not load the NLP NER"


_load_ner()


def removeDuplicateEntities(entities):
    seen = set()
    out = []
    for e in entities:
        text, score = e
        if text not in seen:
            seen.add(text)
            out.append(e)
    return out


def nlp_extract_metadata_doc(doc):

    if not doc:
        return None

    if not doc.doc_file:
        return None

    if os.path.splitext(doc.doc_file.name)[1].lower()[1:] in ["txt", "log", "sld", "xml"]:
        text = None
        with open(doc.doc_file.path, "r") as f:
            text = f.read()
        return _nlp_extract_metadata_core(text=text)
    else:
        return None


def nlp_extract_metadata_dict(d):

    m = {'keywords': set(), 'regions': set()}
    for key in d:
        if d[key]:
            new_metadata = _nlp_extract_metadata_core(d[key])
            m['keywords'] = m['keywords'].union(set(new_metadata['keywords']))
            m['regions'] = m['regions'].union(set(new_metadata['regions']))

    return {'keywords': list(m['keywords']), 'regions': list(m['regions'])}


def _nlp_extract_metadata_core(text=None):

    if text:
        global ner
        from mitie import tokenize

        tokens = tokenize(text)
        entities = ner.extract_entities(tokens)
        locations = []
        organizations = []
        for e in entities:
            range = e[0]
            tag = e[1]
            score = e[2]
            # score_text = "{:0.3f}".format(score)
            entity_text = " ".join(tokens[i] for i in range)
            if tag == "LOCATION":
                locations.append((entity_text, score))
            elif tag == "ORGANIZATION":
                organizations.append((entity_text, score))
            # print tag+" : "+entity_text+" : "+score_text

        # Remove Duplicates
        locations = removeDuplicateEntities(locations)
        organizations = removeDuplicateEntities(organizations)

        # Resolve Locations to Regions
        regions = []
        for location in locations:
            location_text, score = location
            if score > settings.NLP_LOCATION_THRESHOLD:
                try:
                    region = Region.objects.get(name__iexact=location_text)
                    if region:
                        regions.append(region)
                except:
                    pass

        # Resolve organizations to Keywords/Tags
        keywords = []
        for organization in organizations:
            organization_text, score = organization
            try:
                keyword = Tag.objects.get(name__iexact=organization_text)
                if keyword:
                    keywords.append(keyword.name)
            except:
                pass

        return {'regions': regions, 'keywords': keywords}

    else:
        return None
