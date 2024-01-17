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
import re
import logging

from urllib.parse import urlparse, urlencode

from django.conf import settings
from django.template.loader import get_template
from owslib.catalogue.csw2 import CatalogueServiceWeb, namespaces
from owslib.util import http_post
from owslib.etree import etree as dlxml
from owslib.fes import PropertyIsLike, BBox
from geonode.catalogue.backends.base import BaseCatalogueBackend

logger = logging.getLogger(__name__)

TIMEOUT = 10
METADATA_FORMATS = {
    "Atom": ("atom:entry", "http://www.w3.org/2005/Atom"),
    "DIF": ("dif:DIF", "http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/"),
    "Dublin Core": ("csw:Record", "http://www.opengis.net/cat/csw/2.0.2"),
    "ebRIM": ("rim:RegistryObject", "urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0"),
    "FGDC": ("fgdc:metadata", "http://www.opengis.net/cat/csw/csdgm"),
    "ISO": ("gmd:MD_Metadata", "http://www.isotc211.org/2005/gmd"),
}


class Catalogue(CatalogueServiceWeb):
    def __init__(self, *args, **kwargs):
        self.url = kwargs["URL"]
        self.user = None
        self.password = None
        self.type = kwargs["ENGINE"].split(".")[-1]
        self.local = False
        self._group_ids = {}
        self._operation_ids = {}
        self.connected = False
        skip_caps = kwargs.get("skip_caps", True)
        CatalogueServiceWeb.__init__(self, url=self.url, skip_caps=skip_caps)

        upurl = urlparse(self.url)

        self.base = f"{upurl.scheme}://{upurl.netloc}/"

        # User and Password are optional
        if "USER" in kwargs:
            self.user = kwargs["USER"]
        if "PASSWORD" in kwargs:
            self.password = kwargs["PASSWORD"]

    def __enter__(self, *args, **kwargs):
        self.login()
        return self

    def __exit__(self, *args, **kwargs):
        self.logout()

    def login(self):
        NotImplemented

    def logout(self):
        NotImplemented

    def get_by_uuid(self, uuid):
        try:
            self.getrecordbyid([uuid], outputschema=namespaces["gmd"])
        except Exception:
            return None

        if hasattr(self, "records"):
            if len(self.records) < 1:
                return None
            record = list(self.records.values())[0]
            record.keywords = []
            if (
                hasattr(record, "identification")
                and len(record.identification) > 0
                and hasattr(record.identification[0], "keywords")
            ):
                for kw in record.identification[0].keywords:
                    record.keywords.extend(kw.keywords)
            return record
        else:
            return None

    def url_for_uuid(self, uuid, outputschema):
        _query_string = urlencode(
            {
                "request": "GetRecordById",
                "service": "CSW",
                "version": "2.0.2",
                "id": uuid,
                "outputschema": outputschema,
                "elementsetname": "full",
            }
        )
        return f"{self.url}?{_query_string}"

    def urls_for_uuid(self, uuid):
        """returns list of valid GetRecordById URLs for a given record"""
        urls = []
        for mformat in self.formats:
            urls.append(("text/xml", mformat, self.url_for_uuid(uuid, METADATA_FORMATS[mformat][1])))
        return urls

    def csw_gen_xml(self, layer, template):
        id_pname = "dc:identifier"
        if self.type == "deegree":
            id_pname = "apiso:Identifier"
        site_url = settings.SITEURL.rstrip("/") if settings.SITEURL.startswith("http") else settings.SITEURL
        tpl = get_template(template)
        ctx = {
            "CATALOG_METADATA_TEMPLATE": settings.CATALOG_METADATA_TEMPLATE,
            "layer": layer,
            "SITEURL": site_url,
            "id_pname": id_pname,
            "LICENSES_METADATA": getattr(settings, "LICENSES", dict()).get("METADATA", "never"),
        }
        md_doc = tpl.render(context=ctx)
        return md_doc

    def csw_gen_anytext(self, xml):
        """get all element data from an XML document"""
        xml = dlxml.fromstring(xml)
        return " ".join([value.strip() for value in xml.xpath("//text()")])

    def csw_request(self, layer, template):
        md_doc = self.csw_gen_xml(layer, template)
        response = http_post(self.url, md_doc, timeout=TIMEOUT)
        return response

    def create_from_dataset(self, layer):
        response = self.csw_request(layer, "catalogue/transaction_insert.xml")  # noqa
        # TODO: Parse response, check for error report
        return self.url_for_uuid(layer.uuid, namespaces["gmd"])

    def delete_dataset(self, layer):
        response = self.csw_request(layer, "catalogue/transaction_delete.xml")  # noqa
        # TODO: Parse response, check for error report

    def update_dataset(self, layer):
        tmpl = "catalogue/transaction_update.xml"
        response = self.csw_request(layer, tmpl)  # noqa
        # TODO: Parse response, check for error report

    def search(self, keywords, startposition, maxrecords, bbox):
        """CSW search wrapper"""
        formats = []
        for f in self.formats:
            formats.append(METADATA_FORMATS[f][0])

        dataset_query_like = []
        if keywords:
            for _kw in keywords:
                dataset_query_like.append(PropertyIsLike("csw:AnyText", _kw))
        bbox_query = []
        if bbox:
            bbox_query = BBox(bbox)
        return self.getrecords2(
            typenames=" ".join(formats),
            constraints=dataset_query_like + bbox_query,
            startposition=startposition,
            maxrecords=maxrecords,
            outputschema="http://www.isotc211.org/2005/gmd",
            esn="full",
        )

    def normalize_bbox(self, bbox):
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
        result["uuid"] = rec.identifier
        result["title"] = rec.identification[0].title
        result["abstract"] = rec.identification[0].abstract

        keywords = []
        for kw in rec.identification[0].keywords:
            keywords.extend(kw["keywords"])

        result["keywords"] = keywords

        # XXX needs indexing ? how
        result["attribution"] = {"title": "", "href": ""}

        result["name"] = result["uuid"]

        result["bbox"] = {
            "minx": rec.identification[0].bbox.minx,
            "maxx": rec.identification[0].bbox.maxx,
            "miny": rec.identification[0].bbox.miny,
            "maxy": rec.identification[0].bbox.maxy,
        }

        # locate all distribution links
        result["download_links"] = self.extract_links(rec)

        # construct the link to the Catalogue metadata record (not
        # self-indexed)
        result["metadata_links"] = [
            ("text/xml", "ISO", self.url_for_uuid(rec.identifier, "http://www.isotc211.org/2005/gmd"))
        ]

        return result

    def extract_links(self, rec):
        # fetch all distribution links

        links = []
        # extract subset of description value for user-friendly display
        format_re = re.compile(r".*\((.*)(\s*Format*\s*)\).*?")

        if not hasattr(rec, "distribution"):
            return None
        if not hasattr(rec.distribution, "online"):
            return None

        for link_el in rec.distribution.online:
            if "WWW:DOWNLOAD" in link_el.protocol:
                try:
                    extension = link_el.name.split(".")[-1]
                    format = format_re.match(link_el.description).groups()[0]
                    href = link_el.url
                    links.append((extension, format, href))
                except Exception:
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
                rec.links["metadata"] = self.catalogue.urls_for_uuid(uuid)
                rec.links["download"] = self.catalogue.extract_links(rec)
        return rec

    def search_records(self, keywords, start, limit, bbox):
        with self.catalogue:
            bbox = self.catalogue.normalize_bbox(bbox)
            self.catalogue.search(keywords, start + 1, limit, bbox)

            # build results into JSON for API
            results = [self.catalogue.metadatarecord2dict(doc) for v, doc in self.catalogue.records.items()]

            result = {
                "rows": results,
                "total": self.catalogue.results["matches"],
                "next_page": self.catalogue.results.get("nextrecord", 0),
            }

            return result

    def remove_record(self, uuid):
        with self.catalogue:
            catalogue_record = self.catalogue.get_by_uuid(uuid)
            if catalogue_record is None:
                return
            try:
                # this is a bit hacky, delete_dataset expects an instance of the layer
                # model but it just passes it to a Django template so a dict works
                # too.
                self.catalogue.delete_dataset({"uuid": uuid})
            except Exception:
                logger.exception("Couldn't delete Catalogue record during cleanup()")

    def create_record(self, item):
        with self.catalogue:
            record = self.catalogue.get_by_uuid(item.uuid)
            if record is None:
                md_link = self.catalogue.create_from_dataset(item)
                item.metadata_links = [("text/xml", "ISO", md_link)]
            else:
                self.catalogue.update_dataset(item)
