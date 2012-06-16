import re
import urllib, urllib2, cookielib
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from owslib.csw import CatalogueServiceWeb, namespaces
from owslib.util import http_post, nspath
from urlparse import urlparse
from lxml import etree


def metadatarecord2dict(rec, catalogue):
    """
    accepts a node representing a catalogue result 
    record and builds a POD structure representing 
    the search result.
    """

    if rec is None:
        return None
    # Let owslib do some parsing for us...
    result = {}
    result['uuid'] = rec.identifier
    result['title'] = rec.identification.title
    result['abstract'] = rec.identification.abstract

    keywords = []
    for kw in rec.identification.keywords:
        keywords.extend(kw['keywords'])

    result['keywords'] = keywords

    # XXX needs indexing ? how
    result['attribution'] = {'title': '', 'href': ''}

    result['name'] = result['uuid']

    result['bbox'] = {
        'minx': rec.identification.bbox.minx,
        'maxx': rec.identification.bbox.maxx,
        'miny': rec.identification.bbox.miny,
        'maxy': rec.identification.bbox.maxy
        }

    # locate all distribution links
    result['download_links'] = _extract_links(rec)

    # construct the link to the Catalogue metadata record (not self-indexed)
    result['metadata_links'] = [("text/xml", "TC211", catalogue.url_for_uuid(rec.identifier, 'http://www.isotc211.org/2005/gmd'))]

    return result

def _extract_links(rec):
    # fetch all distribution links

    links = []
    # extract subset of description value for user-friendly display
    format_re = re.compile(".*\((.*)(\s*Format*\s*)\).*?")

    if not hasattr(rec, 'distribution'):
        return None
    if not hasattr(rec.distribution, 'online'):
        return None

    for link_el in rec.distribution.online:
        if link_el.protocol == 'WWW:DOWNLOAD-1.0-http--download':
            try:
                extension = link_el.name.split('.')[-1]
                format = format_re.match(link_el.description).groups()[0]
                href = link_el.url
                links.append((extension, format, href))
            except:
                pass
    return links
