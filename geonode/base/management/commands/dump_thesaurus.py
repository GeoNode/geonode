#########################################################################
#
# Copyright (C) 2020 OSGeo
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

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DC, DCTERMS, RDF, SKOS

from geonode.base.models import Thesaurus, ThesaurusKeyword, ThesaurusKeywordLabel, ThesaurusLabel


class Command(BaseCommand):

    help = 'Dump a thesaurus in RDF format'
    formats = sorted(['ttl', 'xml', 'pretty-xml', 'json-ld', 'nt', 'n3', 'trig'])

    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            '-n',
            '--name',
            dest='name',
            help='Dump the thesaurus with the given name')

        parser.add_argument(
            '-f',
            '--format',
            dest='format',
            default='pretty-xml',
            help=f'Format string supported by rdflib, e.g.: pretty-xml (default), {", ".join(self.formats)}'
        )

        parser.add_argument(
            '--default-lang',
            dest='lang',
            default=getattr(settings, 'THESAURUS_DEFAULT_LANG', None),
            help='Default language code for untagged string literals'
        )

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

        if options.get('format') not in self.formats:
            raise CommandError(f"Invalid output format: supported formats are {', '.join(self.formats)}")

        if list:
            self.list_thesauri()
            return

        self.dump_thesaurus(name, options.get('format'), options.get('lang'))

    def list_thesauri(self):
        self.stderr.write(self.style.SUCCESS('LISTING THESAURI'))

        thesaurus_entries = Thesaurus.objects.values_list('identifier', flat=True)
        if len(thesaurus_entries) == 0:
            self.stderr.write(self.style.WARNING('NO ENTRIES FOUND ...'))
            return
        max_id_len = len(max(thesaurus_entries, key=len))

        for t in Thesaurus.objects.order_by('order').all():
            if t.card_max == 0:
                card = 'DISABLED'
            else:
                # DISABLED
                # [0..n]
                card = f'[{t.card_min}..{t.card_max if t.card_max!=-1 else "N"}]  '
            self.stdout.write(f'id:{t.id:2} sort:{t.order:3} {card} name={t.identifier.ljust(max_id_len)} title="{t.title}" URI:{t.about}\n')

    def dump_thesaurus(self, name: str, fmt: str, default_lang: str):

        g = Graph()
        thesaurus = Thesaurus.objects.filter(identifier=name).get()
        scheme = URIRef(thesaurus.about)
        g.add((scheme, RDF.type, SKOS.ConceptScheme))
        g.add((scheme, DC.title, Literal(thesaurus.title, lang=default_lang)))
        g.add((scheme, DC.description, Literal(thesaurus.description, lang=default_lang)))
        g.add((scheme, DCTERMS.issued, Literal(thesaurus.date)))

        for title_label in ThesaurusLabel.objects.filter(thesaurus=thesaurus).all():
            g.add((scheme, DC.title, Literal(title_label.label, lang=title_label.lang)))

        # Concepts
        for keyword in ThesaurusKeyword.objects.filter(thesaurus=thesaurus).all():
            concept = URIRef(keyword.about)
            g.add((concept, RDF.type, SKOS.Concept))
            g.add((concept, SKOS.inScheme, scheme))
            if keyword.alt_label:
                g.add((concept, SKOS.altLabel, Literal(keyword.alt_label, lang=default_lang)))
            for label in ThesaurusKeywordLabel.objects.filter(keyword=keyword).all():
                g.add((concept, SKOS.prefLabel, Literal(label.label, lang=label.lang)))

        self.stdout.write(g.serialize(format=fmt))
