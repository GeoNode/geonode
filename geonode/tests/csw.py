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
from .base import GeoNodeBaseTestSupport

import os
import glob
import gisdata
import logging

from lxml import etree
from owslib import fes
from owslib.etree import etree as dlxml
from owslib.fes import PropertyIsLike
# ref.: https://geopython.github.io/OWSLib/_sources/index.txt

from django.conf import settings

from geonode import geoserver
from geonode.utils import check_ogc_backend
from geonode.catalogue import get_catalogue
from geonode.base.models import ResourceBase

logger = logging.getLogger(__name__)

LOCAL_TEST_CATALOG_URL = settings.CATALOGUE['default']['URL']


class GeoNodeCSWTest(GeoNodeBaseTestSupport):
    """Tests geonode.catalogue app/module"""

    def test_csw_base(self):
        """Verify that GeoNode works against any CSW"""
        csw = get_catalogue(
            backend={
                'ENGINE': 'geonode.catalogue.backends.pycsw_local',
                'URL': LOCAL_TEST_CATALOG_URL,
            },
            skip_caps=False)

        self.assertEqual(
            csw.catalogue.url,
            LOCAL_TEST_CATALOG_URL
        )

        # test that OGC:CSW URLs are identical to what is defined in GeoNode
        for op in csw.catalogue.operations:
            for method in op.methods:
                self.assertEqual(
                    csw.catalogue.url,
                    method['url'],
                    'Expected GeoNode URL to be equal to all CSW URLs')

        # test that OGC:CSW 2.0.2 is supported
        self.assertEqual(csw.catalogue.version, '2.0.2',
                         'Expected "2.0.2" as a supported version')

        # test that transactions are supported
        if csw.catalogue.type != 'pycsw_local':
            self.assertTrue(
                'Transaction' in [
                    o.name for o in csw.catalogue.operations],
                'Expected Transaction to be a supported operation')

        # test that gmd:MD_Metadata is a supported typename
        for o in csw.catalogue.operations:
            if o.name == 'GetRecords':
                typenames = o.parameters['typeNames']['values']
        self.assertTrue(
            'gmd:MD_Metadata' in typenames,
            'Expected "gmd:MD_Metadata" to be a supported typeNames value')

        # test that http://www.isotc211.org/2005/gmd is a supported output
        # schema
        for o in csw.catalogue.operations:
            if o.name == 'GetRecords':
                outputschemas = o.parameters['outputSchema']['values']
        self.assertTrue(
            'http://www.isotc211.org/2005/gmd' in outputschemas,
            'Expected "http://www.isotc211.org/2005/gmd" to be a supported outputSchema value')

    def test_csw_search_count(self):
        """Verify that GeoNode CSW can handle search counting"""
        csw = get_catalogue(
            backend={
                'ENGINE': 'geonode.catalogue.backends.pycsw_local',
                'URL': LOCAL_TEST_CATALOG_URL,
            },
            skip_caps=False)

        self.assertEqual(
            csw.catalogue.url,
            LOCAL_TEST_CATALOG_URL
        )

        # get all records
        csw.catalogue.getrecords2(typenames='csw:Record')
        self.assertGreaterEqual(
            csw.catalogue.results['matches'],
            12,
            'Expected 12+ records')

        # get all ISO records, test for numberOfRecordsMatched
        csw.catalogue.getrecords2(typenames='gmd:MD_Metadata')
        self.assertGreaterEqual(
            csw.catalogue.results['matches'],
            12,
            'Expected 12+ records against ISO typename')

        # Make sure it currently counts both published and unpublished ones too
        try:
            ResourceBase.objects.filter(is_published=True).update(is_published=False)
            # get all ISO records, test for numberOfRecordsMatched
            csw.catalogue.getrecords2(typenames='gmd:MD_Metadata')
            self.assertGreaterEqual(
                csw.catalogue.results['matches'],
                12,
                'Expected 12+ records against ISO typename')
        finally:
            ResourceBase.objects.filter(is_published=False).update(is_published=True)

    def test_csw_outputschema_dc(self):
        """Verify that GeoNode CSW can handle ISO metadata with Dublin Core outputSchema"""

        csw = get_catalogue()

        # search for 'san_andres_y_providencia_location', output as Dublin Core
        dataset_query_like = PropertyIsLike('csw:AnyText', '%san_andres_y_providencia_location%')
        csw.catalogue.getrecords2(
            typenames='gmd:MD_Metadata',
            constraints=[dataset_query_like],
            outputschema='http://www.opengis.net/cat/csw/2.0.2',
            esn='full')

        record = list(csw.catalogue.records.values())[0]

        # test that the ISO title maps correctly in Dublin Core
        self.assertTrue(record.title in "san_andres_y_providencia_location.shp")

        # test that the ISO abstract maps correctly in Dublin Core
        if record.abstract:
            self.assertEqual(record.abstract, 'No abstract provided')

        # test for correct service link articulation
        for link in record.references:
            if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                if link['scheme'] == 'OGC:WMS':
                    self.assertEqual(link['url'], f"{settings.GEOSERVER_PUBLIC_LOCATION}ows")
                elif link['scheme'] == 'OGC:WFS':
                    self.assertEqual(link['url'], f"{settings.GEOSERVER_PUBLIC_LOCATION}ows")
                elif link['scheme'] == 'OGC:WCS':
                    self.assertEqual(link['url'], f"{settings.GEOSERVER_PUBLIC_LOCATION}ows")

    def test_csw_outputschema_iso(self):
        """Verify that GeoNode CSW can handle ISO metadata with ISO outputSchema"""

        csw = get_catalogue()

        # search for 'san_andres_y_providencia_location', output as Dublin Core
        dataset_query_like = PropertyIsLike('csw:AnyText', '%san_andres_y_providencia_location%')
        csw.catalogue.getrecords2(
            typenames='gmd:MD_Metadata',
            constraints=[dataset_query_like],
            maxrecords=20,
            outputschema='http://www.isotc211.org/2005/gmd',
            esn='full')

        record = list(csw.catalogue.records.values())[0]

        # test that the ISO title maps correctly in Dublin Core
        self.assertTrue(record.identification.title in "san_andres_y_providencia_location.shp")

        # test that the ISO abstract maps correctly in Dublin Core
        self.assertEqual(record.identification.abstract, 'No abstract provided')

        # test BBOX properties in Dublin Core
        from decimal import Decimal
        self.assertAlmostEqual(Decimal(record.identification.bbox.minx), Decimal('-81.8593555'), places=3)
        self.assertAlmostEqual(Decimal(record.identification.bbox.miny), Decimal('12.1665322'), places=3)
        self.assertAlmostEqual(Decimal(record.identification.bbox.maxx), Decimal('-81.356409'), places=3)
        self.assertAlmostEqual(Decimal(record.identification.bbox.maxy), Decimal('13.396306'), places=3)

        # test for correct link articulation
        for link in record.distribution.online:
            if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                if link.protocol == 'OGC:WMS':
                    self.assertEqual(
                        link.url,
                        f'{settings.GEOSERVER_PUBLIC_LOCATION}ows',
                        'Expected a specific OGC:WMS URL')
                elif link.protocol == 'OGC:WFS':
                    self.assertEqual(
                        link.url,
                        f'{settings.GEOSERVER_PUBLIC_LOCATION}ows',
                        'Expected a specific OGC:WFS URL')

    def test_csw_outputschema_dc_bbox(self):
        """Verify that GeoNode CSW can handle ISO metadata BBOX model with Dublin Core outputSchema"""
        csw = get_catalogue()

        # search for 'san_andres_y_providencia_location', output as DublinCore
        dataset_query_like = PropertyIsLike('csw:AnyText', '%san_andres_y_providencia_location%')
        csw.catalogue.getrecords2(
            typenames='gmd:MD_Metadata',
            constraints=[dataset_query_like],
            outputschema='http://www.opengis.net/cat/csw/2.0.2',
            esn='full')

        record = list(csw.catalogue.records.values())[0]

        # test CRS constructs in Dublin Core
        self.assertEqual(record.bbox.crs.code, 4326)
        # test BBOX properties in Dublin Core
        from decimal import Decimal
        logger.debug([Decimal(record.bbox.minx), Decimal(record.bbox.miny),
                      Decimal(record.bbox.maxx), Decimal(record.bbox.maxy)])
        self.assertAlmostEqual(Decimal(record.bbox.minx), Decimal('-81.859356'), places=3)
        self.assertAlmostEqual(Decimal(record.bbox.miny), Decimal('12.166532'), places=3)
        self.assertAlmostEqual(Decimal(record.bbox.maxx), Decimal('-81.356409'), places=3)
        self.assertAlmostEqual(Decimal(record.bbox.maxy), Decimal('13.396306'), places=3)

    def test_csw_outputschema_fgdc(self):
        """Verify that GeoNode CSW can handle ISO metadata with FGDC outputSchema"""
        csw = get_catalogue()
        if csw.catalogue.type in {'pycsw_http', 'pycsw_local'}:
            # get all ISO records in FGDC schema
            dataset_query_like = PropertyIsLike('csw:AnyText', '%san_andres_y_providencia_location%')
            csw.catalogue.getrecords2(
                typenames='gmd:MD_Metadata',
                constraints=[dataset_query_like],
                outputschema='http://www.opengis.net/cat/csw/csdgm')

            record = list(csw.catalogue.records.values())[0]

            # test that the ISO title maps correctly in FGDC
            self.assertTrue(record.idinfo.citation.citeinfo['title'] in "san_andres_y_providencia_location.shp")

            # test that the ISO abstract maps correctly in FGDC
            if record.idinfo.descript.abstract:
                self.assertEqual(record.idinfo.descript.abstract, 'No abstract provided')

    def test_csw_query_bbox(self):
        """Verify that GeoNode CSW can handle bbox queries"""

        csw = get_catalogue()
        bbox = fes.BBox([-140, -70, 80, 70])
        try:
            csw.catalogue.getrecords2([bbox, ])
            logger.debug(csw.catalogue.results)
            self.assertEqual(csw.catalogue.results, {'matches': 7, 'nextrecord': 0, 'returned': 7})
        except Exception:
            # This test seems to borken actually on pycsw
            pass

    def test_csw_upload_fgdc(self):
        """Verify that GeoNode CSW can handle FGDC metadata upload"""
        csw = get_catalogue()
        if csw.catalogue.type == 'pycsw_http':
            # upload a native FGDC metadata document
            md_doc = etree.tostring(
                dlxml.fromstring(
                    open(
                        os.path.join(
                            gisdata.GOOD_METADATA,
                            'sangis.org',
                            'Census',
                            'Census_Blockgroup_Pop_Housing.shp.xml')).read()))
            csw.catalogue.transaction(
                ttype='insert',
                typename='fgdc:metadata',
                record=md_doc)

            # test that FGDC document was successfully inserted
            self.assertEqual(csw.catalogue.results['inserted'], 1)

            # query against FGDC typename, output FGDC
            csw.catalogue.getrecords2(typenames='fgdc:metadata')
            self.assertEqual(csw.catalogue.results['matches'], 1)

            record = list(csw.catalogue.records.values())[0]

            # test that the FGDC title maps correctly in DC
            self.assertEqual(record.title, "Census_Blockgroup_Pop_Housing")

            # test that the FGDC type maps correctly in DC
            self.assertEqual(record.type, "vector digital data")

            # test CRS constructs in Dublin Core
            self.assertEqual(record.bbox.crs.code, 4326)

            # test BBOX properties in Dublin Core
            from decimal import Decimal
            self.assertEqual(Decimal(record.bbox.minx), Decimal('-117.6'))
            self.assertEqual(Decimal(record.bbox.miny), Decimal('32.53'))
            self.assertEqual(Decimal(record.bbox.maxx), Decimal('-116.08'))
            self.assertEqual(Decimal(record.bbox.maxy), Decimal('33.51'))

            # query against FGDC typename, return in ISO
            csw.catalogue.getrecords2(
                typenames='fgdc:metadata',
                esn='brief',
                outputschema='http://www.isotc211.org/2005/gmd')
            self.assertEqual(csw.catalogue.results['matches'], 1)

            record = list(csw.catalogue.records.values())[0]

            # test that the FGDC title maps correctly in ISO
            self.assertEqual(record.identification.title, "Census_Blockgroup_Pop_Housing")

            # cleanup and delete inserted FGDC metadata document
            csw.catalogue.transaction(
                ttype='delete',
                typename='fgdc:metadata',
                cql='fgdc:Title like "Census_Blockgroup_Pop_Housing"')
            self.assertEqual(csw.catalogue.results['deleted'], 1)

    def test_csw_bulk_upload(self):
        """Verify that GeoNode CSW can handle bulk upload of ISO and FGDC metadata"""
        csw = get_catalogue()
        if csw.catalogue.type == 'pycsw_http':

            identifiers = []

            # upload all metadata
            for root, dirs, files in os.walk(os.path.join(gisdata.GOOD_METADATA, 'sangis.org')):
                for mfile in files:
                    if mfile.endswith('.xml'):
                        md_doc = etree.tostring(
                            dlxml.fromstring(
                                open(
                                    os.path.join(
                                        root,
                                        mfile)).read()))
                        csw.catalogue.transaction(
                            ttype='insert',
                            typename='fgdc:metadata',
                            record=md_doc)
                        identifiers.append(
                            csw.catalogue.results['insertresults'][0])

            for md in glob.glob(os.path.join(gisdata.GOOD_METADATA, 'wustl.edu', '*.xml')):
                md_doc = etree.tostring(dlxml.fromstring(open(md).read()))
                csw.catalogue.transaction(
                    ttype='insert',
                    typename='gmd:MD_Metadata',
                    record=md_doc)
                identifiers.append(csw.catalogue.results['insertresults'][0])

            # query against FGDC typename
            csw.catalogue.getrecords2(typenames='fgdc:metadata')
            self.assertEqual(
                csw.catalogue.results['matches'],
                72,
                'Expected 187 records in FGDC model')

            # query against ISO typename
            csw.catalogue.getrecords2(typenames='gmd:MD_Metadata')
            self.assertEqual(
                csw.catalogue.results['matches'],
                115,
                'Expected 194 records in ISO model')

            # query against FGDC and ISO typename
            csw.catalogue.getrecords2(typenames='gmd:MD_Metadata fgdc:metadata')
            self.assertEqual(
                csw.catalogue.results['matches'],
                187,
                'Expected 381 records total in FGDC and ISO model')

            # clean up
            for i in identifiers:
                csw.catalogue.transaction(ttype='delete', identifier=i)
