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
            vals['purpose'] = md.identification.purpose
            vals['supplemental_information'] = md.identification.self.supplementalinformation

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

        if hasattr(md.idinfo, 'descript'):
            vals['abstract'] = md.idinfo.descript.abstract
            vals['purpose'] = md.idinfo.descript.purpose
            vals['supplemental_information'] = md.idinfo.descript.supplinf

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

