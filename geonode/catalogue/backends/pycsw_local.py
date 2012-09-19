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

import os
from lxml import etree
from django.conf import settings
from ConfigParser import SafeConfigParser
from owslib.iso import MD_Metadata
from pycsw import server
from geonode.catalogue.backends.generic import CatalogueBackend as GenericCatalogueBackend
from geonode.catalogue.backends.generic import METADATA_FORMATS

# pycsw settings that the user shouldn't have to worry about
CONFIGURATION = {
    'server': {
        'home': '.',
        'url': settings.CATALOGUE['default']['URL'],
        'encoding': 'UTF-8',
        'language': settings.LANGUAGE_CODE,
        'maxrecords': '10',
        #'loglevel': 'DEBUG',
        #'logfile': '/tmp/pycsw.log',
        #'federatedcatalogues': 'http://geo.data.gov/geoportal/csw/discovery',
        #'pretty_print': 'true',
        #'domainquerytype': 'range',
        #'domaincounts': 'true',
        'profiles': 'apiso,atom,dif,ebrim,fgdc',
    },
    'repository': {
        'source': 'geonode',
        'mappings': os.path.abspath(__file__[:-1])
    }
}


MD_CORE_MODEL = {
    'typename': 'pycsw:CoreMetadata',
    'outputschema': 'http://pycsw.org/metadata',
    'mappings': {
        'pycsw:Identifier': 'uuid',
        'pycsw:Typename': 'csw_typename',
        'pycsw:Schema': 'csw_schema',
        'pycsw:MdSource': 'csw_mdsource',
        'pycsw:InsertDate': 'csw_insert_date',
        'pycsw:XML': 'metadata_xml',
        'pycsw:AnyText': 'csw_anytext',
        'pycsw:Language': 'language',
        'pycsw:Title': 'title',
        'pycsw:Abstract': 'abstract',
        'pycsw:Keywords': 'keyword_csv',
        'pycsw:KeywordType': 'keywordstype',
        'pycsw:Format': 'spatial_representation_type',
        'pycsw:Source': 'source',
        'pycsw:Date': 'date',
        'pycsw:Modified': 'last_modified',
        'pycsw:Type': 'csw_type',
        'pycsw:BoundingBox': 'csw_wkt_geometry',
        'pycsw:CRS': 'crs',
        'pycsw:AlternateTitle': 'title_alternate',
        'pycsw:RevisionDate': 'date_revision',
        'pycsw:CreationDate': 'last_modified',
        'pycsw:PublicationDate': 'date_publication',
        'pycsw:OrganizationName': 'uuid',
        'pycsw:SecurityConstraints': 'securityconstraints',
        'pycsw:ParentIdentifier': 'parentidentifier',
        'pycsw:TopicCategory': 'topicategory',
        'pycsw:ResourceLanguage': 'resourcelanguage',
        'pycsw:GeographicDescriptionCode': 'geodescode',
        'pycsw:Denominator': 'denominator',
        'pycsw:DistanceValue': 'distancevalue',
        'pycsw:DistanceUOM': 'distanceuom',
        'pycsw:TempExtent_begin': 'temporal_extent_start',
        'pycsw:TempExtent_end': 'temporal_extent_end',
        'pycsw:ServiceType': 'servicetype',
        'pycsw:ServiceTypeVersion': 'servicetypeversion',
        'pycsw:Operation': 'operation',
        'pycsw:CouplingType': 'couplingtype',
        'pycsw:OperatesOn': 'operateson',
        'pycsw:OperatesOnIdentifier': 'operatesonidentifier',
        'pycsw:OperatesOnName': 'operatesoname',
        'pycsw:Degree': 'degree',
        'pycsw:AccessConstraints': 'accessconstraints',
        'pycsw:OtherConstraints': 'otherconstraints',
        'pycsw:Classification': 'classification',
        'pycsw:ConditionApplyingToAccessAndUse': 'conditionapplyingtoaccessanduse',
        'pycsw:Lineage': 'lineage',
        'pycsw:ResponsiblePartyRole': 'responsiblepartyrole',
        'pycsw:SpecificationTitle': 'specificationtitle',
        'pycsw:SpecificationDate': 'specificationdate',
        'pycsw:SpecificationDateType': 'specificationdatetype',
        'pycsw:Creator': 'creator',
        'pycsw:Publisher': 'publisher',
        'pycsw:Contributor': 'contributor',
        'pycsw:Relation': 'relation',
        'pycsw:Links': 'download_links',
    }
}

class CatalogueBackend(GenericCatalogueBackend):
    def __init__(self, *args, **kwargs):
        super(CatalogueBackend, self).__init__(*args, **kwargs)
        self.catalogue.formats = ['Atom', 'DIF', 'Dublin Core', 'ebRIM', 'FGDC', 'TC211']
        self.catalogue.local = True

    def remove_record(self, uuid):
        pass

    def create_record(self, item):
        pass

    def get_record(self, uuid):
        results = self._csw_local_dispatch(identifier=uuid)
        if len(results) < 1:
            return None

        result = etree.fromstring(results).find('{http://www.isotc211.org/2005/gmd}MD_Metadata')

        if result is None:
            return None

        record = MD_Metadata(result)
        record.keywords = []
        if hasattr(record, 'identification') and hasattr(record.identification, 'keywords'):
            for kw in record.identification.keywords:
                record.keywords.extend(kw['keywords'])

        record.links = {}
        record.links['metadata'] = self.catalogue.urls_for_uuid(uuid)
        record.links['download'] = self.catalogue.extract_links(record)
        return record

    def search_records(self, keywords, start, limit, bbox):
        with self.catalogue:
            lresults = self._csw_local_dispatch(keywords, keywords, start+1, limit, bbox)
            # serialize XML
            e = etree.fromstring(lresults)
            self.catalogue.records = [MD_Metadata(x) for x in e.findall('//{http://www.isotc211.org/2005/gmd}MD_Metadata')]

            # build results into JSON for API
            results = [self.catalogue.metadatarecord2dict(doc) for v, doc in self.catalogue.records.iteritems()]

            result = {
                      'rows': results,
                      'total': e.find('{http://www.opengis.net/cat/csw/2.0.2}SearchResults').attrib.get('numberOfRecordsMatched'),
                      'next_page': e.find('{http://www.opengis.net/cat/csw/2.0.2}SearchResults').attrib.get('nextRecord')
                      }

            return result


    def _csw_local_dispatch(self, keywords=None, start=0, limit=10, bbox=None, identifier=None):
        """
        HTTP-less CSW
        """

        # serialize pycsw settings into SafeConfigParser
        # object for interaction with pycsw
        mdict = dict(settings.PYCSW['CONFIGURATION'], **CONFIGURATION)
        config = SafeConfigParser()
    
        for section, options in mdict.iteritems():
            config.add_section(section)
            for option, value in options.iteritems():
                config.set(section, option, value)
    
        # fake HTTP environment variable
        os.environ['QUERY_STRING'] = ''
    
        # init pycsw
        csw = server.Csw(config)
    
        # fake HTTP method
        csw.requesttype = 'POST'
    
        # fake HTTP request parameters
        if identifier is None:  # it's a GetRecords request
            formats = []
            for f in self.catalogue.formats:
                formats.append(METADATA_FORMATS[f][0])

            csw.kvp = {
                'elementsetname': 'full',
                'typenames': formats,
                'resulttype': 'results',
                'constraintlanguage': 'CQL_TEXT',
                'constraint': 'csw:AnyText like "%%%s%%"' % keywords,
                'outputschema': 'http://www.isotc211.org/2005/gmd',
                'constraint': None,
                'startposition': start,
                'maxrecords': limit
            }
            response = csw.getrecords()
        else:  # it's a GetRecordById request
            csw.kvp = {
                'id': [identifier],
                'outputschema': 'http://www.isotc211.org/2005/gmd',
            }
            response = csw.getrecordbyid()
    
        return etree.tostring(response)
