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

import logging
import re
import urllib
import urllib2
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from owslib.csw import CatalogueServiceWeb, namespaces
from owslib.util import http_post
from urlparse import urlparse
from lxml import etree
from geonode.catalogue.backends.base import BaseCatalogueBackend

logger = logging.getLogger(__name__)

TIMEOUT = 10
METADATA_FORMATS = {'Atom': ('atom:entry', 'http://www.w3.org/2005/Atom'),
                    'DIF': ('dif:DIF', 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/'),
                    'Dublin Core': ('csw:Record', 'http://www.opengis.net/cat/csw/2.0.2'),
                    'ebRIM': ('rim:RegistryObject', 'urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0'),
                    'FGDC': ('fgdc:metadata', 'http://www.opengis.net/cat/csw/csdgm'),
                    'GM03': ('gm03:TRANSFER', 'http://www.interlis.ch/INTERLIS2.3'),
                    'ISO': ('gmd:MD_Metadata', 'http://www.isotc211.org/2005/gmd')
                    }


class Catalogue(CatalogueServiceWeb):
    def __init__(self, *args, **kwargs):
        self.url = kwargs['URL']
        self.user = None
        self.password = None
        self.type = kwargs['ENGINE'].split('.')[-1]
        self.local = False
        self._group_ids = {}
        self._operation_ids = {}
        self.connected = False
        skip_caps = kwargs.get('skip_caps', True)
        CatalogueServiceWeb.__init__(self, url=self.url, skip_caps=skip_caps)

        upurl = urlparse(self.url)

        self.base = '%s://%s/' % (upurl.scheme, upurl.netloc)

        # User and Password are optional
        if 'USER'in kwargs:
            self.user = kwargs['USER']
        if 'PASSWORD' in kwargs:
            self.password = kwargs['PASSWORD']

    def __enter__(self, *args, **kwargs):
        self.login()
        return self

    def __exit__(self, *args, **kwargs):
        self.logout()

    def login(self):
        if self.type == 'geonetwork':
            url = "%sgeonetwork/srv/en/xml.user.login" % self.base
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/plain"
            }
            post = urllib.urlencode({
                "username": self.user,
                "password": self.password
            })
            request = urllib2.Request(url, post, headers)
            self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(), urllib2.HTTPRedirectHandler())
            response = self.opener.open(request)
            doc = etree.fromstring(response.read())
            assert doc.tag == 'ok', "GeoNetwork login failed!"
            self.connected = True

    def logout(self):
        if self.type == 'geonetwork':
            url = "%sgeonetwork/srv/en/xml.user.logout" % self.base
            request = urllib2.Request(url)
            response = self.opener.open(request)  # noqa
            self.connected = False

    def get_by_uuid(self, uuid):
        try:
            self.getrecordbyid([uuid], outputschema=namespaces["gmd"])
        except:
            return None

        if hasattr(self, 'records'):
            if len(self.records) < 1:
                return None
            record = self.records.values()[0]
            record.keywords = []
            if hasattr(record, 'identification') and hasattr(record.identification, 'keywords'):
                for kw in record.identification.keywords:
                    record.keywords.extend(kw['keywords'])
            return record
        else:
            return None

    def url_for_uuid(self, uuid, outputschema):
        return "%s?%s" % (self.url, urllib.urlencode({
            "request": "GetRecordById",
            "service": "CSW",
            "version": "2.0.2",
            "id": uuid,
            "outputschema": outputschema,
            "elementsetname": "full"
        }))

    def urls_for_uuid(self, uuid):
        """returns list of valid GetRecordById URLs for a given record"""

        urls = []
        for mformat in self.formats:
            urls.append(('text/xml', mformat, self.url_for_uuid(uuid, METADATA_FORMATS[mformat][1])))
        return urls

    def csw_gen_xml(self, layer, template):
        id_pname = 'dc:identifier'
        if self.type == 'deegree':
            id_pname = 'apiso:Identifier'

        tpl = get_template(template)
        ctx = Context({
            'layer': layer,
            'SITEURL': settings.SITEURL[:-1],
            'id_pname': id_pname,
            'LICENSES_METADATA': getattr(settings, 'LICENSES', dict()).get('METADATA', 'never')
        })
        md_doc = tpl.render(ctx)
        return md_doc

    def csw_gen_anytext(self, xml):
        """ get all element data from an XML document """
        xml = etree.fromstring(xml)
        return ' '.join([value.strip() for value in xml.xpath('//text()')])

    def csw_request(self, layer, template):

        md_doc = self.csw_gen_xml(layer, template).encode('utf-8')

        if self.type == 'geonetwork':
            headers = {
                "Content-Type": "application/xml; charset=UTF-8",
                "Accept": "text/plain"
            }
            request = urllib2.Request(self.url, md_doc, headers)
            response = self.urlopen(request)
        else:
            response = http_post(self.url, md_doc, timeout=TIMEOUT)
        return response

    def create_from_layer(self, layer):
        response = self.csw_request(layer, "catalogue/transaction_insert.xml")
        # TODO: Parse response, check for error report

        if self.type == 'geonetwork':

            # set layer.uuid based on what GeoNetwork returns
            # this is needed for inserting FGDC metadata in GN

            exml = etree.fromstring(response.read())
            identifier = exml.find('{%s}InsertResult/{%s}BriefRecord/identifier'
                                   % (namespaces['csw'], namespaces['csw'])).text
            layer.uuid = identifier

            # Turn on the "view" permission (aka publish) for
            # the "all" group in GeoNetwork so that the layer
            # will be searchable via CSW without admin login.
            # all other privileges are set to False for all
            # groups.
            self.set_metadata_privs(layer.uuid, {"all":  {"view": True}})

        return self.url_for_uuid(layer.uuid, namespaces['gmd'])

    def delete_layer(self, layer):
        response = self.csw_request(layer, "catalogue/transaction_delete.xml")  # noqa
        # TODO: Parse response, check for error report

    def update_layer(self, layer):
        tmpl = 'catalogue/transaction_update.xml'

        if self.type == 'geonetwork':
            tmpl = 'catalogue/transaction_update_gn.xml'

        response = self.csw_request(layer, tmpl)  # noqa

        # TODO: Parse response, check for error report

    def set_metadata_privs(self, uuid, privileges):
        """
        set the full set of geonetwork privileges on the item with the
        specified uuid based on the dictionary given of the form:
        {
          'group_name1': {'operation1': True, 'operation2': True, ...},
          'group_name2': ...
        }

        all unspecified operations and operations for unspecified groups
        are set to False.
        """

        # XXX This is a fairly ugly workaround that makes
        # requests similar to those made by the GeoNetwork
        # admin based on the recommendation here:
        # http://bit.ly/ccVEU7

        if self.type == 'geonetwork':
            get_dbid_url = '%sgeonetwork/srv/en/portal.search.present?%s' % \
                           (self.base, urllib.urlencode({'uuid': uuid}))

            # get the id of the data.
            request = urllib2.Request(get_dbid_url)
            response = self.urlopen(request)
            doc = etree.fromstring(response.read())
            data_dbid = doc.find('metadata/{http://www.fao.org/geonetwork}info/id').text

            # update group and operation info if needed
            if len(self._group_ids) == 0:
                self._group_ids = self._geonetwork_get_group_ids()
            if len(self._operation_ids) == 0:
                self._operation_ids = self._geonetwork_get_operation_ids()

            #  build params that represent the privilege configuration
            priv_params = {
                "id": data_dbid,  # "uuid": layer.uuid, # you can say this instead in newer versions of GN
            }
            for group, privs in privileges.items():
                group_id = self._group_ids[group.lower()]
                for op, state in privs.items():
                    if state is not True:
                        continue
                    op_id = self._operation_ids[op.lower()]
                    priv_params['_%s_%s' % (group_id, op_id)] = 'on'

            # update all privileges
            update_privs_url = "%sgeonetwork/srv/en/metadata.admin?%s" % (self.base, urllib.urlencode(priv_params))
            request = urllib2.Request(update_privs_url)
            response = self.urlopen(request)

            # TODO: check for error report

    def _geonetwork_get_group_ids(self):
        """
        helper to fetch the set of geonetwork
        groups.
        """
        # get the ids of the groups.
        get_groups_url = "%sgeonetwork/srv/en/xml.info?%s" % (self.base, urllib.urlencode({'type': 'groups'}))
        request = urllib2.Request(get_groups_url)
        response = self.urlopen(request)
        doc = etree.fromstring(response.read())
        groups = {}
        for gp in doc.findall('groups/group'):
            groups[gp.find('name').text.lower()] = gp.attrib['id']
        return groups

    def _geonetwork_get_operation_ids(self):
        """
        helper to fetch the set of geonetwork
        'operations' (privileges)
        """
        # get the ids of the operations
        get_ops_url = "%sgeonetwork/srv/en/xml.info?%s" % (self.base, urllib.urlencode({'type': 'operations'}))
        request = urllib2.Request(get_ops_url)
        response = self.urlopen(request)
        doc = etree.fromstring(response.read())
        ops = {}
        for op in doc.findall('operations/operation'):
            ops[op.find('name').text.lower()] = op.attrib['id']
        return ops

    def urlopen(self, request):
        if self.opener is None:
            raise Exception("No URL opener defined in geonetwork module!!")
        else:
            return self.opener.open(request)

    def search(self, keywords, startposition, maxrecords, bbox):
        """CSW search wrapper"""
        formats = []
        for f in self.formats:
            formats.append(METADATA_FORMATS[f][0])

        return self.getrecords(typenames=' '.join(formats),
                               keywords=keywords,
                               startposition=startposition,
                               maxrecords=maxrecords,
                               bbox=bbox,
                               outputschema='http://www.isotc211.org/2005/gmd',
                               esn='full')

    def normalize_bbox(self, bbox):
        """
        fix bbox axis order
        GeoNetwork accepts x/y
        pycsw accepts y/x
        """

        if self.type == 'geonetwork':
            return bbox
        else:  # swap coords per standard
            return [bbox[1], bbox[0], bbox[3], bbox[2]]

    def metadatarecord2dict(self, rec):
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
        result['download_links'] = self.extract_links(rec)

        # construct the link to the Catalogue metadata record (not self-indexed)
        result['metadata_links'] = [("text/xml", "ISO", self.url_for_uuid(rec.identifier,
                                                                          'http://www.isotc211.org/2005/gmd'))]

        return result

    def extract_links(self, rec):
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


class CatalogueBackend(BaseCatalogueBackend):
    def __init__(self, *args, **kwargs):
        self.catalogue = Catalogue(*args, **kwargs)

    def get_record(self, uuid):
        with self.catalogue:
            rec = self.catalogue.get_by_uuid(uuid)
            if rec is not None:
                rec.links = dict()
                rec.links['metadata'] = self.catalogue.urls_for_uuid(uuid)
                rec.links['download'] = self.catalogue.extract_links(rec)
        return rec

    def search_records(self, keywords, start, limit, bbox):
        with self.catalogue:
            bbox = self.catalogue.normalize_bbox(bbox)
            self.catalogue.search(keywords, start+1, limit, bbox)

            # build results into JSON for API
            results = [self.catalogue.metadatarecord2dict(doc) for v, doc in self.catalogue.records.iteritems()]

            result = {'rows': results,
                      'total': self.catalogue.results['matches'],
                      'next_page': self.catalogue.results.get('nextrecord', 0)}

            return result

    def remove_record(self, uuid):
        with self.catalogue:
            catalogue_record = self.catalogue.get_by_uuid(uuid)
            if catalogue_record is None:
                return
            try:
                # this is a bit hacky, delete_layer expects an instance of the layer
                # model but it just passes it to a Django template so a dict works
                # too.
                self.catalogue.delete_layer({"uuid": uuid})
            except:
                logger.exception('Couldn\'t delete Catalogue record during cleanup()')

    def create_record(self, item):
        with self.catalogue:
            record = self.catalogue.get_by_uuid(item.uuid)
            if record is None:
                md_link = self.catalogue.create_from_layer(item)
                item.metadata_links = [("text/xml", "ISO", md_link)]
            else:
                self.catalogue.update_layer(item)
