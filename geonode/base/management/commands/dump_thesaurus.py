#########################################################################
#
# Copyright (C) 2021 OSGeo
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

from lxml import etree

from django.core.management.base import BaseCommand, CommandError

from geonode.base.models import Thesaurus, ThesaurusKeyword, ThesaurusKeywordLabel, ThesaurusLabel

RDF_URI = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
XML_URI = 'http://www.w3.org/XML/1998/namespace'
SKOS_URI = 'http://www.w3.org/2004/02/skos/core#'
DC_URI = 'http://purl.org/dc/elements/1.1/'
DCTERMS_URI = 'http://purl.org/dc/terms/'

RDF_NS = f'{{{RDF_URI}}}'
XML_NS = f'{{{XML_URI}}}'
SKOS_NS = f'{{{SKOS_URI}}}'
DC_NS = f'{{{DC_URI}}}'
DCTERMS_NS = f'{{{DCTERMS_URI}}}'


class Command(BaseCommand):

    help = 'Dump a thesaurus in RDF format'

    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            '--name',
            dest='name',
            help='Dump the thesaurus with the given name')

        # Named (optional) arguments
        parser.add_argument(
            '-l',
            '--list',
            action="store_true",
            dest='list',
            default=False,
            help='List available thesauri')

    def handle(self, **options):

        name = options.get('name')
        list = options.get('list')

        if not name and not list:
            raise CommandError("Missing identifier name for the thesaurus (--name)")

        if list:
            self.list_thesauri()
            return

        self.dump_thesaurus(name)

    def list_thesauri(self):
        print('LISTING THESAURI')
        max_id_len = len(max(Thesaurus.objects.values_list('identifier', flat=True), key=len))

        for t in Thesaurus.objects.order_by('order').all():
            if t.card_max == 0:
                card = 'DISABLED'
            else:
                # DISABLED
                # [0..n]
                card = f'[{t.card_min}..{t.card_max if t.card_max!=-1 else "N"}]  '
            print(f'id:{t.id:2} sort:{t.order:3} {card} name={t.identifier.ljust(max_id_len)} title="{t.title}" URI:{t.about}')

    def dump_thesaurus(self, name):
        thesaurus = Thesaurus.objects.filter(identifier=name).get()

        ns = {
            None: SKOS_URI,
            'rdf': RDF_URI,
            'xml': XML_URI,
            'dc': DC_URI,
            'dcterms': DCTERMS_URI
        }

        root = etree.Element(f"{RDF_NS}RDF", nsmap=ns)
        concept_scheme = etree.SubElement(root, f"{SKOS_NS}ConceptScheme")
        concept_scheme.set(f"{RDF_NS}about", thesaurus.about)

        # Default title
        # <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">GEMET - INSPIRE themes, version 1.0</dc:title>
        title = etree.SubElement(concept_scheme, f"{DC_NS}title")
        title.text = thesaurus.title

        # Localized titles
        # <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">Limitations on public access</dc:title>
        for ltitle in ThesaurusLabel.objects.filter(thesaurus=thesaurus).all():
            title = etree.SubElement(concept_scheme, f"{DC_NS}title")
            title.set(f"{XML_NS}lang", ltitle.lang)
            title.text = ltitle.label

        d = etree.SubElement(concept_scheme, f"{DCTERMS_NS}issued")
        d.text = thesaurus.date
        d = etree.SubElement(concept_scheme, f"{DCTERMS_NS}modified")
        d.text = thesaurus.date

        # Concepts
        for keyword in ThesaurusKeyword.objects.filter(thesaurus=thesaurus).all():
            concept = etree.SubElement(concept_scheme, f"{SKOS_NS}Concept")
            if keyword.about:
                concept.set(f"{RDF_NS}about", keyword.about)

            if keyword.alt_label:
                # <skos:altLabel>cp</skos:altLabel>
                label = etree.SubElement(concept, f"{SKOS_NS}altLabel")
                label.text = keyword.alt_label

            for label in ThesaurusKeywordLabel.objects.filter(keyword=keyword).all():
                # <skos:prefLabel xml:lang="en">Geographical grid systems</skos:prefLabel>
                pref_label = etree.SubElement(concept, f"{SKOS_NS}prefLabel")
                pref_label.set(f"{XML_NS}lang", label.lang)
                pref_label.text = label.label

        etree.dump(root, pretty_print=True)
