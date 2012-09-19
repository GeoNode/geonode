# -*- coding: utf-8 -*-
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

"""Utilities for managing GeoNode resource metadata
"""

# Standard Modules
import logging
import datetime
from lxml import etree

from django.conf import settings

# Geonode functionality
from geonode import GeoNodeException
# OWSLib functionality
from owslib.csw import CswRecord
from owslib.iso import MD_Metadata
from owslib.fgdc import Metadata

logger = logging.getLogger(__name__)

def update_metadata(layer_uuid, xml, saved_layer):
    """Update metadata XML document with GeoNode specific values"""
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
    layer_updated = saved_layer.date.strftime('%Y-%m-%d')

    if tagname == 'Record': # Dublin Core
        dc_ns = '{http://purl.org/dc/elements/1.1/}'
        dct_ns ='{http://purl.org/dc/terms/}'

        children = exml.getchildren()

        # set/update identifier
        xname = exml.find('%sidentifier' % dc_ns)
        if xname is None: # doesn't exist, insert it
            value = etree.Element('%sidentifier' % dc_ns)
            value.text = layer_uuid
            children.insert(0, value)
        else: # exists, update it
            xname.text = layer_uuid

        xname = exml.find('%smodified' % dct_ns)
        if xname is None: # doesn't exist, insert it
            value = etree.Element('%smodified' % dct_ns)
            value.text = layer_updated
            children.insert(3, value)
        else: # exists, update it
            xname.text = layer_updated

        # set/update URLs
        http_link = etree.Element('%sreferences' % dct_ns, scheme='WWW:LINK-1.0-http--link')
        http_link.text = '%s%s' % (settings.SITEURL, saved_layer.get_absolute_url())
        children.insert(-2, http_link)

        for link in saved_layer.link_set.all():
            http_link = etree.Element('%sreferences' % dct_ns, scheme='WWW:DOWNLOAD-1.0-http--download')
            http_link.text = link.url
            children.insert(-2, http_link)

    elif tagname == 'MD_Metadata':
        gmd_ns = 'http://www.isotc211.org/2005/gmd'
        gco_ns = 'http://www.isotc211.org/2005/gco'

        # set/update gmd:fileIdentifier
        xname = exml.find('{%s}fileIdentifier' % gmd_ns)
        if xname is None: # doesn't exist, insert it
            children = exml.getchildren()
            fileid = etree.Element('{%s}fileIdentifier' % gmd_ns)
            etree.SubElement(fileid, '{%s}CharacterString' % gco_ns).text = layer_uuid
            children.insert(0, fileid)
        else: # gmd:fileIdentifier exists, check for gco:CharacterString
            value = xname.find('{%s}CharacterString' % gco_ns)
            if value is None:
                etree.SubElement(xname, '{%s}CharacterString' % gco_ns).text = layer_uuid
            else:
                value.text = layer_uuid

        # set/update gmd:dateStamp
        xname = exml.find('{%s}dateStamp' % gmd_ns)
        if xname is None: # doesn't exist, insert it
            children = exml.getchildren()
            datestamp = etree.Element('{%s}dateStamp' % gmd_ns)
            etree.SubElement(datestamp, '{%s}DateTime' % gco_ns).text = layer_updated
            children.insert(4, datestamp)
        else: # gmd:dateStamp exists, check for gco:Date or gco:DateTime
            value = xname.find('{%s}Date' % gco_ns)
            value2 = xname.find('{%s}DateTime' % gco_ns)

            if value is None and value2 is not None: # set gco:DateTime
                value2.text = layer_updated
            elif value is not None and value2 is None: # set gco:Date
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

        for extension, dformat, dprotocol, link in saved_layer.download_links():
            online = etree.SubElement(transopts2, '{%s}onLine' % gmd_ns)
            online2 = etree.SubElement(online, '{%s}CI_OnlineResource' % gmd_ns)
            linkage = etree.SubElement(online2, '{%s}linkage' % gmd_ns)

            etree.SubElement(linkage, '{%s}URL' % gmd_ns).text = link or ''
            protocol = etree.SubElement(online2, '{%s}protocol' % gmd_ns)
            etree.SubElement(protocol, '{%s}CharacterString' % gco_ns).text = dprotocol
            lname = etree.SubElement(online2, '{%s}name' % gmd_ns)
            etree.SubElement(lname, '{%s}CharacterString' % gco_ns).text = extension or ''
            ldesc = etree.SubElement(online2, '{%s}description' % gmd_ns)
            etree.SubElement(ldesc, '{%s}CharacterString' % gco_ns).text = dformat or ''

        children.insert(-2, distinfo)

    elif tagname == 'metadata': # FGDC
        # set/update identifier
        xname = exml.find('idinfo/datasetid')
        if xname is None: # doesn't exist, insert it
            children = exml.find('idinfo').getchildren()
            value = etree.Element('datasetid')
            value.text = layer_uuid
            children.insert(0, value)
        else: # exists, update it
            xname.text = layer_uuid

        xname = exml.find('metainfo/metd')
        if xname is None: # doesn't exist, insert it
            value = etree.Element('metd')
            value.text = layer_updated
            exml.find('metainfo').append(value)
        else: # exists, update it
            xname.text = layer_updated

        # set/update URLs
        citeinfo = exml.find('idinfo/citation/citeinfo')
        http_link = etree.Element('onlink')
        http_link.attrib['type'] = 'WWW:LINK-1.0-http--link'
        http_link.text = '%s%s' % (settings.SITEURL, saved_layer.get_absolute_url())
        citeinfo.append(http_link)

        for extension, dformat, protocol, link in saved_layer.download_links():
            http_link = etree.Element('onlink')
            http_link.attrib['type'] = protocol
            http_link.text = link
            citeinfo.append(http_link)

    else:
        raise GeoNodeException('Unsupported metadata format')

    return etree.tostring(exml)

def set_metadata(xml):
    """Generate dict of model properties based on XML metadata"""

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

    vals = {}

    if tagname == 'MD_Metadata':  # ISO
        md = MD_Metadata(exml)

        vals['csw_typename'] = 'gmd:MD_Metadata'
        vals['csw_schema'] = 'http://www.isotc211.org/2005/gmd'
        vals['language'] = md.language
        vals['spatial_representation_type'] = md.hierarchy
        vals['date'] = sniff_date(md.datestamp.strip())

        if hasattr(md, 'identification'):
            vals['title'] = md.identification.title
            vals['abstract'] = md.identification.abstract

            vals['temporal_extent_start'] = md.identification.temporalextent_start
            vals['temporal_extent_end'] = md.identification.temporalextent_end

            if len(md.identification.topiccategory) > 0:
                vals['topic_category'] = md.identification.topiccategory[0]

            if (hasattr(md.identification, 'keywords') and
            len(md.identification.keywords) > 0):
                if None not in md.identification.keywords[0]['keywords']:
                    keywords = md.identification.keywords[0]['keywords']

            if len(md.identification.securityconstraints) > 0:
                vals['constraints_use'] = md.identification.securityconstraints[0]
            if len(md.identification.otherconstraints) > 0:
                vals['constraints_other'] = md.identification.otherconstraints[0]

            vals['purpose'] = md.identification.purpose

        if hasattr(md.identification, 'dataquality'):
            vals['data_quality_statement'] = md.dataquality.lineage

    elif tagname == 'metadata':  # FGDC
        md = Metadata(exml)

        vals['csw_typename'] = 'fgdc:metadata'
        vals['csw_schema'] = 'http://www.opengis.net/cat/csw/csdgm'
        vals['spatial_representation_type'] = md.idinfo.citation.citeinfo['geoform']

        if hasattr(md, 'idinfo'):
            vals['title'] = md.idinfo.citation.citeinfo['title']
            vals['abstract'] = md.idinfo.descript.abstract

        if hasattr(md.idinfo, 'keywords'):
            if md.idinfo.keywords.theme:
                keywords = md.idinfo.keywords.theme[0]['themekey']

        if hasattr(md.idinfo.timeperd, 'timeinfo'):
            if hasattr(md.idinfo.timeperd.timeinfo, 'rngdates'):
                vals['temporal_extent_start'] = sniff_date(md.idinfo.timeperd.timeinfo.rngdates.begdate.strip())
                vals['temporal_extent_end'] = sniff_date(md.idinfo.timeperd.timeinfo.rngdates.enddate.strip())

        vals['constraints_other'] = md.idinfo.useconst
        vals['date'] = sniff_date(md.metainfo.metd.strip())

    elif tagname == 'Record':  # Dublin Core
        md = CswRecord(exml)

        vals['csw_typename'] = 'csw:Record'
        vals['csw_schema'] = 'http://www.opengis.net/cat/csw/2.0.2'
        vals['language'] = md.language
        vals['spatial_representation_type'] = md.type
        keywords = md.subjects
        vals['temporal_extent_start'] = md.temporal
        vals['temporal_extent_end'] = md.temporal
        vals['constraints_other'] = md.license
        vals['date'] = sniff_date(md.modified.strip())
        vals['title'] = md.title
        vals['abstract'] = md.abstract
    else:
        raise RuntimeError('Unsupported metadata format')

    return [vals, keywords]

def sniff_date(datestr):
    """
    Attempt to parse date into datetime.datetime object

    Possible inputs:

    '20001122'
    '2000-11-22'
    '2000-11-22T11:11:11Z'
    '2000-11-22T'
    """

    for f in ('%Y%m%d','%Y-%m-%d','%Y-%m-%dT%H:%M:%SZ','%Y-%m-%dT','%Y/%m/%d'):
        try:
            return datetime.datetime.strptime(datestr, f)
        except ValueError:
            pass

