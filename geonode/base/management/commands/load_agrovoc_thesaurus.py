#########################################################################
#
# Copyright (C) 2022 Leibniz-Centre for Agricultural Landscape
# Research (ZALF) e.V. - Marcel Wallschlaeger
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

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.core.management.base import BaseCommand, CommandError
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import SKOS, DCTERMS
from rdflib.util import guess_format

from geonode.base.models import Thesaurus, ThesaurusKeyword, ThesaurusKeywordLabel


class SKOS_XL():
    ''' additional definitions(SKOS-XL) not included in rdflib '''
    prefLabel = URIRef("http://www.w3.org/2008/05/skos-xl#prefLabel")
    literalForm = URIRef('http://www.w3.org/2008/05/skos-xl#literalForm')


# only including concepts for the AGROVOC core concept scheme
AGROVOC_ConceptSchemeURI = URIRef("http://aims.fao.org/aos/agrovoc")

# To reduce storage this script only includes languages supported by geonode and not all languages included in the AGROVOC,
SUPPORTED_LANGUAGES = ['fr', 'de', 'en', 'it', 'es']


class Command(BaseCommand):

    help = '(Down)Load a AGROVOC in RDF format into DB'

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

        parser.add_argument(
            '--title',
            dest='title',
            default='AGROVOC',
            help="title to set in the base_thesaurus table for the agrovoc thesaurus")

        parser.add_argument(
            '--description',
            dest='description',
            default="""
            AGROVOC is a multilingual and controlled vocabulary designed to cover concepts and terminology under FAO's areas of interest. 
            """,
            help="description to set in the base_thesaurus table for the agrovoc thesaurus")

    def handle(self, **options):

        input_file = options.get('file')
        name = options.get('name')

        title = options.get('title')
        description = options.get('description')

        dryrun = options.get('dryrun')

        if not input_file:
            raise CommandError("Missing thesaurus rdf file path (--file)")

        if not name:
            raise CommandError("Missing identifier name for the thesaurus (--name)")
        
        t_query = Thesaurus.objects.filter(title=title)
        if len(t_query) > 0:
            raise CommandError("Thesaurus with title: {title} already exists ...") 
        
        self.load_thesaurus(input_file=input_file,
                            name=name,
                            store=not dryrun,
                            title=title,
                            description=description)

    def load_thesaurus(self, input_file: str, name: str, store: bool, title: str, description: str):

        g = Graph()

        # if the input_file is an UploadedFile object rather than a file path the Graph.parse()
        # method may not have enough info to correctly guess the type; in this case supply the
        # name, which should include the extension, to guess_format manually...
        rdf_format = None
        if isinstance(input_file, UploadedFile):
            self.stderr.write(self.style.WARNING(f"Guessing RDF format from {input_file.name}..."))
            rdf_format = guess_format(input_file.name)

        self.stderr.write(self.style.SUCCESS(f'Starting to parsed file: {input_file} ...'))
        g.parse(input_file, format=rdf_format)
        self.stderr.write(self.style.SUCCESS(f'Successful parsed file: {input_file} ...'))

        # make date confirm to geonode thesaurus database model
        thesaurus_date = Literal(g.value(AGROVOC_ConceptSchemeURI, DCTERMS.modified, None, default="")).toPython()
        thesaurus_date = thesaurus_date.replace(tzinfo=None).isoformat()

        # define Thesaurus metadata for AGROVOC
        thesaurus = Thesaurus()
        thesaurus.identifier = name
        thesaurus.description = description
        thesaurus.title = title
        thesaurus.about = AGROVOC_ConceptSchemeURI
        thesaurus.date = thesaurus_date

        if store:
            thesaurus.save()

        self.stderr.write(self.style.SUCCESS(f'Thesaurus "{title}", desc: {description} issued at {thesaurus_date}'))

        # skipping thesaurus label due to no thesaurus metadata in agrovoc found

        for concept in g.subjects(SKOS.inScheme, AGROVOC_ConceptSchemeURI):
            about = str(concept)

            # loading default lang from settings
            default_lang = getattr(settings, 'THESAURUS_DEFAULT_LANG', 'en')

            alt_label = get_default_language_preflabel(g, concept, default_lang)
            if alt_label is None:
                self.stderr.write(self.style.ERROR(f'could not find preflabel for concept ({concept}) in THESAURUS_DEFAULT_LANG({default_lang}), skipping entry ...'))
                continue

            tk = ThesaurusKeyword()
            tk.thesaurus = thesaurus
            tk.about = about
            tk.alt_label = alt_label
            if store:
                tk.save()

            i = 0
            for pref_label_element in g.objects(concept, SKOS_XL.prefLabel):
                pref_label = Literal(g.value(pref_label_element, SKOS_XL.literalForm, None))
                lang = pref_label.language
                if lang not in SUPPORTED_LANGUAGES:
                    continue

                label = str(pref_label)
                tkl = ThesaurusKeywordLabel()
                tkl.keyword = tk
                tkl.lang = lang
                tkl.label = label
                i += 1
                if store:
                    try:
                        tkl.save()
                    except:
                        self.stderr.write(self.style.ERROR(f'could not add label: {label} with language: {lang}) to database, skipping entry ...'))

            #self.stderr.write(self.style.SUCCESS(f' set alt_label: {alt_label}: ({i})'))


def get_default_language_preflabel(g: Graph, concept: URIRef, default_lang: str) -> str:
    '''searching for preflabel with default lang '''

    for label in g.objects(concept, SKOS_XL.prefLabel):
        pref_label = Literal(g.value(label, SKOS_XL.literalForm, None))
        language = pref_label.language
        if language == default_lang:
            return str(pref_label)
    return None
