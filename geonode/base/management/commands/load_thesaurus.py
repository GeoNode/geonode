# -*- coding: utf-8 -*-
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

import xml.etree.ElementTree as etree

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from geonode.base.models import Thesaurus, ThesaurusKeyword, ThesaurusKeywordLabel


class Command(BaseCommand):

    help = 'Load a thesaurus in RDF format into DB'

    option_list = BaseCommand.option_list + (
        make_option(
            '-d',
            '--dry-run',
            action="store_true",
            dest='dryrun',
            default=False,
            help='Only parse and print the thesaurus file, without perform insertion in the DB.'),
        make_option(
            '--name',
            dest='name',
            type="string",
            help='Identifier name for the thesaurus in this GeoNode instance.'),
        make_option(
            '--file',
            dest='file',
            type="string",
            help='Full path to a thesaurus in RDF format.'))

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

        ABOUT_ATTRIB = '{' + RDF_URI + '}about'
        LANG_ATTRIB = '{' + XML_URI + '}lang'

        ns = {
            'rdf': RDF_URI,
            'foaf': 'http://xmlns.com/foaf/0.1/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/',
            'skos': 'http://www.w3.org/2004/02/skos/core#'
        }

        tfile = etree.parse(input_file)
        root = tfile.getroot()

        scheme = root.find('skos:ConceptScheme', ns)
        if not scheme:
            raise CommandError("ConceptScheme not found in file")

        title = scheme.find('dc:title', ns).text
        descr = scheme.find('dc:description', ns).text
        date_issued = scheme.find('dcterms:issued', ns).text

        print 'Thesaurus "{}" issued on {}'.format(title, date_issued)

        thesaurus = Thesaurus()
        thesaurus.identifier = name

        thesaurus.title = title
        thesaurus.description = descr
        thesaurus.date = date_issued

        if store:
            thesaurus.save()

        for concept in root.findall('skos:Concept', ns):
            about = concept.attrib.get(ABOUT_ATTRIB)
            alt_label = concept.find('skos:altLabel', ns).text

            print 'Concept {} ({})'.format(alt_label, about)

            tk = ThesaurusKeyword()
            tk.thesaurus = thesaurus
            tk.about = about
            tk.alt_label = alt_label

            if store:
                tk.save()

            for pref_label in concept.findall('skos:prefLabel', ns):
                lang = pref_label.attrib.get(LANG_ATTRIB)
                label = pref_label.text

                print u'    Label {}: {}'.format(lang, label)

                tkl = ThesaurusKeywordLabel()
                tkl.keyword = tk
                tkl.lang = lang
                tkl.label = label

                if store:
                    tkl.save()

    def create_fake_thesaurus(self, name):
        thesaurus = Thesaurus()
        thesaurus.identifier = name

        thesaurus.title = "Title: " + name
        thesaurus.description = "SAMPLE FAKE THESAURUS USED FOR TESTING"
        thesaurus.date = "2016-10-01"

        thesaurus.save()

        for keyword in ['aaa', 'bbb', 'ccc']:
            tk = ThesaurusKeyword()
            tk.thesaurus = thesaurus
            tk.about = keyword + '_about'
            tk.alt_label = keyword + '_alt'
            tk.save()

            for l in ['it', 'en', 'es']:
                tkl = ThesaurusKeywordLabel()
                tkl.keyword = tk
                tkl.lang = l
                tkl.label = keyword + "_l_" + l + "_t_" + name
                tkl.save()
