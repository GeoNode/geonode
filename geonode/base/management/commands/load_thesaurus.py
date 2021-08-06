#########################################################################
#
# Copyright (C) 2016 OSGeo
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

from typing import List
from defusedxml import lxml as dlxml
from django.conf import settings

from django.core.management.base import BaseCommand, CommandError

from geonode.base.models import Thesaurus, ThesaurusKeyword, ThesaurusKeywordLabel, ThesaurusLabel


class Command(BaseCommand):

    help = 'Load a thesaurus in RDF format into DB'

    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            '-d',
            '--dry-run',
            action="store_true",
            dest='dryrun',
            default=False,
            help='Only parse and print the thesaurus file, without perform insertion in the DB.')

        parser.add_argument(
            '--name',
            dest='name',
            help='Identifier name for the thesaurus in this GeoNode instance.')

        parser.add_argument(
            '--file',
            dest='file',
            help='Full path to a thesaurus in RDF format.')

    def handle(self, **options):

        input_file = options.get('file')
        name = options.get('name')
        dryrun = options.get('dryrun')

        if not input_file:
            raise CommandError("Missing thesaurus rdf file path (--file)")

        if not name:
            raise CommandError("Missing identifier name for the thesaurus (--name)")

        if name.startswith('fake'):
            self.create_fake_thesaurus(name)
        else:
            self.load_thesaurus(input_file, name, not dryrun)

    def load_thesaurus(self, input_file, name, store):

        RDF_URI = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
        XML_URI = 'http://www.w3.org/XML/1998/namespace'

        ABOUT_ATTRIB = f"{{{RDF_URI}}}about"
        LANG_ATTRIB = f"{{{XML_URI}}}lang"

        ns = {
            'rdf': RDF_URI,
            'foaf': 'http://xmlns.com/foaf/0.1/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/',
            'skos': 'http://www.w3.org/2004/02/skos/core#'
        }

        tfile = dlxml.parse(input_file)
        root = tfile.getroot()

        scheme = root.find('skos:ConceptScheme', ns)
        if not scheme:
            raise CommandError("ConceptScheme not found in file")

        titles = scheme.findall('dc:title', ns)

        default_lang = getattr(settings, 'THESAURUS_DEFAULT_LANG', None)
        available_lang = get_all_lang_available_with_title(titles, LANG_ATTRIB)
        thesaurus_title = determinate_value(available_lang, default_lang)

        descr = scheme.find('dc:description', ns).text if scheme.find('dc:description', ns) else thesaurus_title
        date_issued = scheme.find('dcterms:issued', ns).text
        about = scheme.attrib.get(ABOUT_ATTRIB)

        print(f'Thesaurus "{thesaurus_title}" issued at {date_issued}')

        thesaurus = Thesaurus()
        thesaurus.identifier = name

        thesaurus.title = thesaurus_title
        thesaurus.description = descr
        thesaurus.about = about
        thesaurus.date = date_issued

        if store:
            thesaurus.save()

        for lang in available_lang:
            if lang[0] is not None:
                thesaurus_label = ThesaurusLabel()
                thesaurus_label.lang = lang[0]
                thesaurus_label.label = lang[1]
                thesaurus_label.thesaurus = thesaurus
                thesaurus_label.save()

        for concept in root.findall('skos:Concept', ns):
            about = concept.attrib.get(ABOUT_ATTRIB)
            alt_label = concept.find('skos:altLabel', ns)
            if alt_label is not None:
                alt_label = alt_label.text
            else:
                concepts = concept.findall('skos:prefLabel', ns)
                available_lang = get_all_lang_available_with_title(concepts, LANG_ATTRIB)
                alt_label = determinate_value(available_lang, default_lang)

            print(f'Concept {alt_label} ({about})')

            tk = ThesaurusKeyword()
            tk.thesaurus = thesaurus
            tk.about = about
            tk.alt_label = alt_label

            if store:
                tk.save()

            for pref_label in concept.findall('skos:prefLabel', ns):
                lang = pref_label.attrib.get(LANG_ATTRIB)
                label = pref_label.text

                print(f'    Label {lang}: {label}')

                tkl = ThesaurusKeywordLabel()
                tkl.keyword = tk
                tkl.lang = lang
                tkl.label = label

                if store:
                    tkl.save()

    def create_fake_thesaurus(self, name):
        thesaurus = Thesaurus()
        thesaurus.identifier = name

        thesaurus.title = f"Title: {name}"
        thesaurus.description = "SAMPLE FAKE THESAURUS USED FOR TESTING"
        thesaurus.date = "2016-10-01"

        thesaurus.save()

        for keyword in ['aaa', 'bbb', 'ccc']:
            tk = ThesaurusKeyword()
            tk.thesaurus = thesaurus
            tk.about = f"{keyword}_about"
            tk.alt_label = f"{keyword}_alt"
            tk.save()

            for _l in ['it', 'en', 'es']:
                tkl = ThesaurusKeywordLabel()
                tkl.keyword = tk
                tkl.lang = _l
                tkl.label = f"{keyword}_l_{_l}_t_{name}"
                tkl.save()


def get_all_lang_available_with_title(items: List, LANG_ATTRIB: str):
    return [(item.attrib.get(LANG_ATTRIB), item.text) for item in items]


def determinate_value(available_lang: List, default_lang: str):
    sorted_lang = sorted(available_lang, key=lambda lang: '' if lang[0] is None else lang[0])
    for item in sorted_lang:
        if item[0] is None:
            return item[1]
        elif item[0] == default_lang:
            return item[1]
    return available_lang[0][1]
