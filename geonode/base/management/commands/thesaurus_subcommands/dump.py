from lxml import etree
import os
import sys
from functools import reduce

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DC, DCTERMS, RDF, SKOS

from django.db.models import Q, QuerySet
from django.core.management.base import CommandError

from geonode.base.models import Thesaurus, ThesaurusKeyword, ThesaurusKeywordLabel, ThesaurusLabel

DUMP_FORMAT_SORTED = "sorted-xml"
DUMP_FORMAT_DEFAULT = DUMP_FORMAT_SORTED
DUMP_FORMATS = sorted([DUMP_FORMAT_SORTED, "ttl", "xml", "pretty-xml", "json-ld", "nt", "n3", "trig"])


def dump_thesaurus(
    identifier: str, fmt: str, default_lang: str = "en", include_list=None, exclude_list=None, output_file=None
):
    thesaurus = Thesaurus.objects.filter(identifier=identifier).first()
    if not thesaurus:
        raise CommandError(f"Thesaurus not found -- id: {identifier}")

    # Concepts
    tk_qs = ThesaurusKeyword.objects.filter(thesaurus=thesaurus)
    if include_list:
        if any((((f.count("*") > 1) or (not f.startswith("*") and not f.endswith("*"))) for f in include_list)):
            raise CommandError("Filtering is only allowed with a single '*' as prefix or suffix")
        filters = (
            Q(about__startswith=f.replace("*", "")) if f.endswith("*") else Q(about__endswith=f.replace("*", ""))
            for f in include_list
        )
        tk_qs = tk_qs.filter(reduce(lambda x, y: x | y, filters))

    if exclude_list:
        if any((((f.count("*") > 1) or (not f.startswith("*") and not f.endswith("*"))) for f in exclude_list)):
            raise CommandError("Filtering is only allowed with a single '*' as prefix or suffix")
        filters = (
            Q(about__startswith=f.replace("*", "")) if f.endswith("*") else Q(about__endswith=f.replace("*", ""))
            for f in exclude_list
        )
        tk_qs = tk_qs.exclude(reduce(lambda x, y: x | y, filters))
    tk_qs = tk_qs.order_by("about")

    if not fmt or fmt == DUMP_FORMAT_SORTED:
        dump_thesaurus_sorted(thesaurus, tk_qs, default_lang, output_file)
    else:
        dump_thesaurus_rdflib(thesaurus, tk_qs, fmt, default_lang, output_file)


RDF_URI = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
XML_URI = "http://www.w3.org/XML/1998/namespace"
SKOS_URI = "http://www.w3.org/2004/02/skos/core#"
DC_URI = "http://purl.org/dc/elements/1.1/"
DCTERMS_URI = "http://purl.org/dc/terms/"

RDF_NS = f"{{{RDF_URI}}}"
XML_NS = f"{{{XML_URI}}}"
SKOS_NS = f"{{{SKOS_URI}}}"
DC_NS = f"{{{DC_URI}}}"
DCTERMS_NS = f"{{{DCTERMS_URI}}}"


def dump_thesaurus_sorted(thesaurus: Thesaurus, tk_qs: QuerySet, default_lang: str = "en", output_file=None):

    ns = {None: SKOS_URI, "rdf": RDF_URI, "xml": XML_URI, "dc": DC_URI, "dcterms": DCTERMS_URI}

    root = etree.Element(f"{RDF_NS}RDF", nsmap=ns)
    concept_scheme = etree.SubElement(root, f"{SKOS_NS}ConceptScheme")
    concept_scheme.set(f"{RDF_NS}about", thesaurus.about)

    # Default title
    # <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">GEMET - INSPIRE themes, version 1.0</dc:title>
    title = etree.SubElement(concept_scheme, f"{DC_NS}title")
    title.text = thesaurus.title

    # Localized titles
    # <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">Limitations on public access</dc:title>
    for ltitle in ThesaurusLabel.objects.filter(thesaurus=thesaurus).order_by("lang").all():
        title = etree.SubElement(concept_scheme, f"{DC_NS}title")
        title.set(f"{XML_NS}lang", ltitle.lang)
        title.text = ltitle.label

    d = etree.SubElement(concept_scheme, f"{DCTERMS_NS}issued")
    d.text = thesaurus.date
    d = etree.SubElement(concept_scheme, f"{DCTERMS_NS}modified")
    d.text = thesaurus.date

    cnt_k = cnt_kl = 0

    # Concepts
    for keyword in tk_qs.all():
        cnt_k += 1
        concept = etree.SubElement(root, f"{SKOS_NS}Concept")
        if keyword.about:
            concept.set(f"{RDF_NS}about", keyword.about)

        inscheme = etree.SubElement(concept, f"{SKOS_NS}inScheme")
        inscheme.set(f"{RDF_NS}resource", thesaurus.about)

        if keyword.alt_label:
            # <skos:altLabel>cp</skos:altLabel>
            label = etree.SubElement(concept, f"{SKOS_NS}altLabel")
            label.text = keyword.alt_label

        for label in ThesaurusKeywordLabel.objects.filter(keyword=keyword).order_by("lang").all():
            cnt_kl += 1
            # <skos:prefLabel xml:lang="en">Geographical grid systems</skos:prefLabel>
            pref_label = etree.SubElement(concept, f"{SKOS_NS}prefLabel")
            pref_label.set(f"{XML_NS}lang", label.lang)
            pref_label.text = label.label

    if output_file:
        etree.ElementTree(root).write(output_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        # with open(output_file, mode='w', encoding='utf-8') as out_file:
        #     root.write(root, out=out_file)
    else:
        etree.dump(root, pretty_print=True)
        # out = etree.canonicalize(root)
        # sys.stderr.write(out)

    sys.stderr.write(f"Thesaurus '{thesaurus.identifier}' exported\n")
    sys.stderr.write(f"- Keywords exported: {cnt_k}\n")
    sys.stderr.write(f"- Labels exported:   {cnt_kl}\n")


def dump_thesaurus_rdflib(thesaurus: Thesaurus, tk_qs: QuerySet, fmt: str, default_lang: str = "en", output_file=None):

    g = Graph()
    scheme = URIRef(thesaurus.about)
    g.add((scheme, RDF.type, SKOS.ConceptScheme))
    g.add((scheme, DC.title, Literal(thesaurus.title, lang=default_lang)))
    g.add((scheme, DC.description, Literal(thesaurus.description, lang=default_lang)))
    g.add((scheme, DCTERMS.issued, Literal(thesaurus.date)))

    for title_label in ThesaurusLabel.objects.filter(thesaurus=thesaurus).all():
        g.add((scheme, DC.title, Literal(title_label.label, lang=title_label.lang)))

    cnt_k = cnt_kl = 0

    for keyword in tk_qs.all():
        cnt_k += 1
        concept = URIRef(keyword.about)
        g.add((concept, RDF.type, SKOS.Concept))
        g.add((concept, SKOS.inScheme, scheme))
        if keyword.alt_label:
            g.add((concept, SKOS.altLabel, Literal(keyword.alt_label, lang=default_lang)))
        for label in ThesaurusKeywordLabel.objects.filter(keyword=keyword).all():
            cnt_kl += 1
            g.add((concept, SKOS.prefLabel, Literal(label.label, lang=label.lang)))

    if output_file:
        output_file = os.path.abspath(output_file)
        if not os.path.isdir(os.path.dirname(output_file)):
            raise CommandError(f"Can not write to output dir: {os.path.dirname(output_file)}")

    out = g.serialize(format=fmt, destination=output_file)

    if output_file is None:
        sys.stdouterr.write(out)

    sys.stderr.write(f"Thesaurus '{thesaurus.identifier}' exported\n")
    sys.stderr.write(f"- Keywords exported: {cnt_k}\n")
    sys.stderr.write(f"- Labels exported:   {cnt_kl}\n")
