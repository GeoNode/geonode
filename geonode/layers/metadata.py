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

# Geonode functionality
from geonode import GeoNodeException
# OWSLib functionality
from owslib.csw import CswRecord
from owslib.iso import MD_Metadata
from owslib.fgdc import Metadata

LOGGER = logging.getLogger(__name__)


def set_metadata(xml):
    """Generate dict of model properties based on XML metadata"""

    # check if document is XML
    try:
        exml = etree.fromstring(xml)
    except Exception, err:
        raise GeoNodeException(
            'Uploaded XML document is not XML: %s' % str(err))

    # check if document is an accepted XML metadata format
    try:
        tagname = exml.tag.split('}')[1]
    except IndexError:
        tagname = exml.tag

    if tagname == 'MD_Metadata':  # ISO
        vals, keywords = iso2dict(exml)
    elif tagname == 'metadata':  # FGDC
        vals, keywords = fgdc2dict(exml)
    elif tagname == 'Record':  # Dublin Core
        vals, keywords = dc2dict(exml)
    else:
        raise RuntimeError('Unsupported metadata format')
    if vals["date"] is None:
        vals["date"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    return [vals, keywords]


def iso2dict(exml):
    """generate dict of properties from gmd:MD_Metadata"""

    vals = {}
    keywords = []

    mdata = MD_Metadata(exml)
    vals['csw_typename'] = 'gmd:MD_Metadata'
    vals['csw_schema'] = 'http://www.isotc211.org/2005/gmd'
    vals['language'] = mdata.language
    vals['spatial_representation_type'] = mdata.hierarchy
    vals['date'] = sniff_date(mdata.datestamp)

    if hasattr(mdata, 'identification'):
        vals['title'] = mdata.identification.title
        vals['abstract'] = mdata.identification.abstract
        vals['purpose'] = mdata.identification.purpose
        if mdata.identification.supplementalinformation is not None:
            vals['supplemental_information'] = \
                mdata.identification.supplementalinformation

        vals['temporal_extent_start'] = \
            mdata.identification.temporalextent_start
        vals['temporal_extent_end'] = \
            mdata.identification.temporalextent_end

        if len(mdata.identification.topiccategory) > 0:
            vals['topic_category'] = mdata.identification.topiccategory[0]

        if (hasattr(mdata.identification, 'keywords') and
        len(mdata.identification.keywords) > 0):
            if None not in mdata.identification.keywords[0]['keywords']:
                keywords = mdata.identification.keywords[0]['keywords']

        if len(mdata.identification.securityconstraints) > 0:
            vals['constraints_use'] = \
                mdata.identification.securityconstraints[0]
        if len(mdata.identification.otherconstraints) > 0:
            vals['constraints_other'] = \
                mdata.identification.otherconstraints[0]

        vals['purpose'] = mdata.identification.purpose

    if mdata.dataquality is not None:
        vals['data_quality_statement'] = mdata.dataquality.lineage

    return [vals, keywords]


def fgdc2dict(exml):
    """generate dict of properties from FGDC metadata"""

    vals = {}
    keywords = []

    mdata = Metadata(exml)
    vals['csw_typename'] = 'fgdc:metadata'
    vals['csw_schema'] = 'http://www.opengis.net/cat/csw/csdgm'

    if hasattr(mdata.idinfo, 'citation'):
        if hasattr(mdata.idinfo.citation, 'citeinfo'):
            vals['spatial_representation_type'] = \
                mdata.idinfo.citation.citeinfo['geoform']
            vals['title'] = mdata.idinfo.citation.citeinfo['title']

    if hasattr(mdata.idinfo, 'descript'):
        vals['abstract'] = mdata.idinfo.descript.abstract
        vals['purpose'] = mdata.idinfo.descript.purpose
        if mdata.idinfo.descript.supplinf is not None:
            vals['supplemental_information'] = mdata.idinfo.descript.supplinf

    if hasattr(mdata.idinfo, 'keywords'):
        if mdata.idinfo.keywords.theme:
            keywords = mdata.idinfo.keywords.theme[0]['themekey']

    if hasattr(mdata.idinfo.timeperd, 'timeinfo'):
        if hasattr(mdata.idinfo.timeperd.timeinfo, 'rngdates'):
            vals['temporal_extent_start'] = \
                sniff_date(mdata.idinfo.timeperd.timeinfo.rngdates.begdate)
            vals['temporal_extent_end'] = \
                sniff_date(mdata.idinfo.timeperd.timeinfo.rngdates.enddate)

    vals['constraints_other'] = mdata.idinfo.useconst
    raw_date = mdata.metainfo.metd
    if raw_date is not None:
        vals['date'] = sniff_date(raw_date)

    return [vals, keywords]


def dc2dict(exml):
    """generate dict of properties from csw:Record"""

    vals = {}
    keywords = []

    mdata = CswRecord(exml)
    vals['csw_typename'] = 'csw:Record'
    vals['csw_schema'] = 'http://www.opengis.net/cat/csw/2.0.2'
    vals['language'] = mdata.language
    vals['spatial_representation_type'] = mdata.type
    keywords = mdata.subjects
    vals['temporal_extent_start'] = mdata.temporal
    vals['temporal_extent_end'] = mdata.temporal
    vals['constraints_other'] = mdata.license
    vals['date'] = sniff_date(mdata.modified)
    vals['title'] = mdata.title
    vals['abstract'] = mdata.abstract

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

    dateformats = ('%Y%m%d', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%SZ',
                   '%Y-%m-%dT', '%Y/%m/%d')

    for dfmt in dateformats:
        try:
            return datetime.datetime.strptime(datestr.strip(), dfmt)
        except ValueError:
            pass
