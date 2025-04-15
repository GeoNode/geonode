import os
import sys
from functools import reduce

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DC, DCTERMS, RDF, SKOS

from django.db.models import Q
from django.core.management.base import CommandError

from geonode.base.models import Thesaurus, ThesaurusKeyword, ThesaurusKeywordLabel, ThesaurusLabel

DUMP_FORMATS = sorted(["ttl", "xml", "pretty-xml", "json-ld", "nt", "n3", "trig"])


def dump_thesaurus(
    identifier: str, fmt: str, default_lang: str = "en", include_list=None, exclude_list=None, output_file=None
):
    thesaurus = Thesaurus.objects.filter(identifier=identifier).first()
    if not thesaurus:
        raise CommandError(f"Thesaurus not found -- id: {identifier}")

    g = Graph()
    scheme = URIRef(thesaurus.about)
    g.add((scheme, RDF.type, SKOS.ConceptScheme))
    g.add((scheme, DC.title, Literal(thesaurus.title, lang=default_lang)))
    g.add((scheme, DC.description, Literal(thesaurus.description, lang=default_lang)))
    g.add((scheme, DCTERMS.issued, Literal(thesaurus.date)))

    for title_label in ThesaurusLabel.objects.filter(thesaurus=thesaurus).all():
        g.add((scheme, DC.title, Literal(title_label.label, lang=title_label.lang)))

    # Concepts
    qs = ThesaurusKeyword.objects.filter(thesaurus=thesaurus)
    if include_list:
        if any((((f.count("*") > 1) or (not f.startswith("*") and not f.endswith("*"))) for f in include_list)):
            raise CommandError("Filtering is only allowed with a single '*' as prefix or suffix")
        filters = (
            Q(about__startswith=f.replace("*", "")) if f.endswith("*") else Q(about__endswith=f.replace("*", ""))
            for f in include_list
        )
        qs = qs.filter(reduce(lambda x, y: x | y, filters))

    if exclude_list:
        if any((((f.count("*") > 1) or (not f.startswith("*") and not f.endswith("*"))) for f in exclude_list)):
            raise CommandError("Filtering is only allowed with a single '*' as prefix or suffix")
        filters = (
            Q(about__startswith=f.replace("*", "")) if f.endswith("*") else Q(about__endswith=f.replace("*", ""))
            for f in exclude_list
        )
        qs = qs.exclude(reduce(lambda x, y: x | y, filters))

    for keyword in qs.all():
        concept = URIRef(keyword.about)
        g.add((concept, RDF.type, SKOS.Concept))
        g.add((concept, SKOS.inScheme, scheme))
        if keyword.alt_label:
            g.add((concept, SKOS.altLabel, Literal(keyword.alt_label, lang=default_lang)))
        for label in ThesaurusKeywordLabel.objects.filter(keyword=keyword).all():
            g.add((concept, SKOS.prefLabel, Literal(label.label, lang=label.lang)))

    if output_file:
        output_file = os.path.abspath(output_file)
        if not os.path.isdir(os.path.dirname(output_file)):
            raise CommandError(f"Can not write to output dir: {os.path.dirname(output_file)}")

    out = g.serialize(format=fmt, destination=output_file)

    if output_file is None:
        sys.stderr.write(out)
