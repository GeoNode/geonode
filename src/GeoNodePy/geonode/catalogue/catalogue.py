import urllib, urllib2, cookielib
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from owslib.csw import CatalogueServiceWeb, namespaces
from owslib.util import http_post, nspath
from urlparse import urlparse
from lxml import etree

connection = settings.CSW['default']

class Catalogue(CatalogueServiceWeb):
    def __init__(self, skip_caps=True):
        self.type = connection['type']
        self.url = connection['url']
        self.user = connection['username']
        self.password = connection['password']
        self._group_ids = {}
        self._operation_ids = {}
        self.connected = False

        CatalogueServiceWeb.__init__(self, url=self.url, skip_caps=skip_caps)

        upurl = urlparse(self.url)

        self.base = '%s://%s/' % (upurl.scheme, upurl.netloc)

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
            self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(),
                    urllib2.HTTPRedirectHandler())
            response = self.opener.open(request)
            doc = etree.fromstring(response.read())
            assert doc.tag == 'ok', "GeoNetwork login failed!"
            self.connected = True

    def logout(self):
        if self.type == 'geonetwork':
            url = "%sgeonetwork/srv/en/xml.user.logout" % self.base
            request = urllib2.Request(url)
            response = self.opener.open(request)
            self.connected = False

    def get_by_uuid(self, uuid):
        try:
            self.getrecordbyid([uuid], outputschema=namespaces["gmd"])
        except:
            return None
    
        if hasattr(self, 'records'):
            recs = self.records
            return recs.values()[0] if len(recs) > 0 else None
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
        for mformat in connection['formats']:
            urls.append({mformat: self.url_for_uuid(uuid, settings.METADATA_FORMATS[mformat])})
        return urls

    def csw_request(self, layer, template):
        tpl = get_template(template)
        ctx = Context({
            'layer': layer,
            'SITEURL': settings.SITEURL[:-1],
        })
        md_doc = tpl.render(ctx)
        md_doc = md_doc.encode("utf-8")

        if self.type == 'geonetwork':
            headers = {
                "Content-Type": "application/xml; charset=UTF-8",
                "Accept": "text/plain"
            }
            request = urllib2.Request(self.url, md_doc, headers)
            response = self.urlopen(request)
        else:
            response = http_post(self.url, md_doc)
        return response

    def create_from_layer(self, layer):
        response = self.csw_request(layer, "maps/csw/transaction_insert.xml")
        # TODO: Parse response, check for error report

        if self.type == 'geonetwork':

            # set layer.uuid based on what GeoNetwork returns
            # this is needed for inserting FGDC metadata in GN

            exml = etree.fromstring(response.read())
            identifier = exml.find('{%s}InsertResult/{%s}BriefRecord/identifier' % (namespaces['csw'], namespaces['csw'])).text
            layer.uuid = identifier

            # Turn on the "view" permission (aka publish) for
            # the "all" group in GeoNetwork so that the layer
            # will be searchable via CSW without admin login.
            # all other privileges are set to False for all 
            # groups.
            self.set_metadata_privs(layer.uuid, {"all":  {"view": True}})
        
        return "%s?%s" % (self.url, urllib.urlencode({
            "request": "GetRecordById",
            "service": "CSW",
            "version": "2.0.2",
            "outputschema": "http://www.isotc211.org/2005/gmd",
            "elementsetname": "full",
            "id": layer.uuid
        }))

    def delete_layer(self, layer):
        response = self.csw_request(layer, "maps/csw/transaction_delete.xml")
        # TODO: Parse response, check for error report

    def update_layer(self, layer):
        tmpl = 'maps/csw/transaction_update.xml'

        if self.type == 'geonetwork':
            tmpl = 'maps/csw/transaction_update_gn.xml'

        response = self.csw_request(layer, tmpl)

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
            get_dbid_url = '%sgeonetwork/srv/en/portal.search.present?%s' % (self.base, urllib.urlencode({'uuid': uuid}))
    
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
    
            # build params that represent the privilege configuration
            priv_params = {
                "id": data_dbid, # "uuid": layer.uuid, # you can say this instead in newer versions of GN 
            }
            for group, privs in privileges.items():
                group_id = self._group_ids[group.lower()]
                for op, state in privs.items():
                    if state != True:
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

    def search(keywords, startposition, maxrecords, bbox):
        """CSW search wrapper"""
        return self.getrecords(typenames='gmd:MD_Metadata csw:Record dif:DIF fgdc:metadata',keywords=keywords, startposition=start+1, maxrecords=limit, bbox=bbox, outputschema='http://www.isotc211.org/2005/gmd', esn='full')

def normalize_bbox(bbox):
    """
    fix bbox axis order
    GeoNetwork accepts x/y
    pycsw accepts y/x
    """

    if connection['type'] == 'geonetwork': 
        return kw['bbox']
    else:  # swap coords per standard
        return [kw['bbox'][1], kw['bbox'][0], kw['bbox'][3], kw['bbox'][2]]

def update_metadata(layer_uuid, xml, saved_layer):
    """Update metadata XML with GeoNode specific information"""
    logger.info('>>> Step XML. If an XML metadata document was passed, process it')
    # Step XML.  If an XML metadata document is uploaded,
    # parse the XML metadata and update uuid and URLs as per the content model

    # check if document is XML
    try:
        exml = etree.fromstring(xml)
    except Exception, err:
        raise GeoNodeException('Uploaded XML document is not XML: %s' % str(err))

    # check if document is an accepted XML metadata format
    try:
        tagname = exml.tag.split('}')[1]
    except:
        tagname = exml.tag

    # update relevant XML
    layer_updated = saved_layer.date.strftime('%Y-%m-%dT%H:%M:%SZ') 

    if catalogue_connection['non_iso_xml_upload_enabled'] is False:
        raise GeoNodeException('Only ISO XML is supported')

    if tagname == 'Record':  # Dublin Core
        dc_ns = '{http://purl.org/dc/elements/1.1/}'
        dct_ns ='{http://purl.org/dc/terms/}'

        children = exml.getchildren()

        # set/update identifier
        xname = exml.find('%sidentifier' % dc_ns)
        if xname is None:  # doesn't exist, insert it
            value = etree.Element('%sidentifier' % dc_ns)
            value.text = layer_uuid
            children.insert(0, value)
        else:  # exists, update it
            xname.text = layer_uuid

        xname = exml.find('%smodified' % dct_ns)
        if xname is None:  # doesn't exist, insert it
            value = etree.Element('%smodified' % dct_ns)
            value.text = layer_updated
            children.insert(3, value)
        else:  # exists, update it
            xname.text = layer_updated

        # set/update URLs
        http_link = etree.Element('%sreferences' % dct_ns, scheme='WWW:LINK-1.0-http--link')
        http_link.text = '%s%s' % (settings.SITEURL, saved_layer.get_absolute_url())
        children.insert(-2, http_link)

        for extension, dformat, link in saved_layer.download_links():
            http_link = etree.Element('%sreferences' % dct_ns, scheme='WWW:DOWNLOAD-1.0-http--download')
            http_link.text = link
            children.insert(-2, http_link)

        from owslib.csw import CswRecord
        # set django properties
        csw_exml = CswRecord(exml)
        md_title = csw_exml.title
        md_abstract = csw_exml.abstract

    elif tagname == 'MD_Metadata':
        gmd_ns = 'http://www.isotc211.org/2005/gmd'
        gco_ns = 'http://www.isotc211.org/2005/gco'

        # set/update gmd:fileIdentifier
        xname = exml.find('{%s}fileIdentifier' % gmd_ns)
        if xname is None:  # doesn't exist, insert it
            children = exml.getchildren()
            fileid = etree.Element('{%s}fileIdentifier' % gmd_ns)
            etree.SubElement(fileid, '{%s}CharacterString' % gco_ns).text = layer_uuid
            children.insert(0, fileid)
        else:  # gmd:fileIdentifier exists, check for gco:CharacterString
            value = xname.find('{%s}CharacterString' % gco_ns)
            if value is None:
                etree.SubElement(xname, '{%s}CharacterString' % gco_ns).text = layer_uuid
            else:
                value.text = layer_uuid

        # set/update gmd:dateStamp
        xname = exml.find('{%s}dateStamp' % gmd_ns)
        if xname is None:  # doesn't exist, insert it
            children = exml.getchildren()
            datestamp = etree.Element('{%s}dateStamp' % gmd_ns)
            etree.SubElement(datestamp, '{%s}DateTime' % gco_ns).text = layer_updated
            children.insert(4, datestamp)
        else:  # gmd:dateStamp exists, check for gco:Date or gco:DateTime
            value = xname.find('{%s}Date' % gco_ns)
            value2 = xname.find('{%s}DateTime' % gco_ns)

            if value is None and value2 is not None:  # set gco:DateTime
                value2.text = layer_updated
            elif value is not None and value2 is None:  # set gco:Date
                value.text = saved_layer.date.strftime('%Y-%m-%d')
            elif value is None and value2 is None:
                etree.SubElement(xname, '{%s}DateTime' % gco_ns).text = layer_updated

        # set/update URLs
        children = exml.getchildren()
        distinfo = etree.Element('{%s}distributionInfo' % gmd_ns)
        distinfo2 = etree.SubElement(distinfo, '{%s}MD_Distribution' % gmd_ns)
        transopts = etree.SubElement(distinfo2, '{%s}transferOptions' % gmd_ns)
        transopts2 = etree.SubElement(transopts, '{%s}MD_DigitalTransferOptions' % gmd_ns)

        online = etree.SubElement(transopts2, '{%s}onLine' % gmd_ns)
        online2 = etree.SubElement(online, '{%s}CI_OnlineResource' % gmd_ns)
        linkage = etree.SubElement(online2, '{%s}linkage' % gmd_ns)
        etree.SubElement(linkage, '{%s}URL' % gmd_ns).text = '%s%s' % (settings.SITEURL, saved_layer.get_absolute_url())
        protocol = etree.SubElement(online2, '{%s}protocol' % gmd_ns)
        etree.SubElement(protocol, '{%s}CharacterString' % gco_ns).text = 'WWW:LINK-1.0-http--link'

        for extension, dformat, link in saved_layer.download_links():
            online = etree.SubElement(transopts2, '{%s}onLine' % gmd_ns)
            online2 = etree.SubElement(online, '{%s}CI_OnlineResource' % gmd_ns)
            linkage = etree.SubElement(online2, '{%s}linkage' % gmd_ns)

            etree.SubElement(linkage, '{%s}URL' % gmd_ns).text = link or ''
            protocol = etree.SubElement(online2, '{%s}protocol' % gmd_ns)
            etree.SubElement(protocol, '{%s}CharacterString' % gco_ns).text = 'WWW:DOWNLOAD-1.0-http--download'
            lname = etree.SubElement(online2, '{%s}name' % gmd_ns)
            etree.SubElement(lname, '{%s}CharacterString' % gco_ns).text = extension or ''
            ldesc = etree.SubElement(online2, '{%s}description' % gmd_ns)
            etree.SubElement(ldesc, '{%s}CharacterString' % gco_ns).text = dformat or ''

        children.insert(-2, distinfo)

        from owslib.iso import MD_Metadata
        iso_exml = MD_Metadata(exml)
        md_title = iso_exml.identification.title
        md_abstract = iso_exml.identification.abstract

    elif tagname == 'metadata':  # FGDC
        # set/update identifier
        xname = exml.find('idinfo/datasetid')
        if xname is None:  # doesn't exist, insert it
            children = exml.find('idinfo').getchildren()
            value = etree.Element('datasetid')
            value.text = layer_uuid
            children.insert(0, value)
        else:  # exists, update it
            xname.text = layer_uuid

        xname = exml.find('metainfo/metd')
        if xname is None:  # doesn't exist, insert it
            value = etree.Element('metd')
            value.text = layer_updated
            exml.find('metainfo').append(value)
        else:  # exists, update it
            xname.text = layer_updated

        # set/update URLs
        citeinfo = exml.find('idinfo/citation/citeinfo')
        http_link = etree.Element('onlink')
        http_link.attrib['type'] = 'WWW:LINK-1.0-http--link'
        http_link.text = '%s%s' % (settings.SITEURL, saved_layer.get_absolute_url())
        citeinfo.append(http_link)

        for extension, dformat, link in saved_layer.download_links():
            http_link = etree.Element('onlink')
            http_link.attrib['type'] = 'WWW:DOWNLOAD-1.0-http--download'
            http_link.text = link
            citeinfo.append(http_link)

        from owslib.fgdc import Metadata as FGDC_Metadata


        with open('/tmp/fff.txt','w') as ff:
            ff.write(str(etree.tostring(exml)))

        fgdc_exml = FGDC_Metadata(exml)
        md_title = fgdc_exml.idinfo.citation.citeinfo['title'] 
        md_abstract = fgdc_exml.idinfo.descript.abstract

    else:
        raise GeoNodeException('Unsupported metadata format')

    return [etree.tostring(exml), md_title, md_abstract]

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
