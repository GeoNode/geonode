# -*- coding: utf-8 -*-
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

from geonode import geoserver, qgis_server
from geonode.utils import check_ogc_backend
from geonode.catalogue import get_catalogue

logger = logging.getLogger(__name__)


class GeoNodeCSWTest(GeoNodeBaseTestSupport):
    """Tests geonode.catalogue app/module"""

    def test_csw_base(self):
        """Verify that GeoNode works against any CSW"""

        csw = get_catalogue(skip_caps=False)

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

        csw = get_catalogue(skip_caps=False)

        # get all records
        csw.catalogue.getrecords(typenames='csw:Record')
        self.assertEqual(
            csw.catalogue.results['matches'],
            16,
            'Expected 16 records')

        # get all ISO records, test for numberOfRecordsMatched
        csw.catalogue.getrecords(typenames='gmd:MD_Metadata')
        self.assertEqual(
            csw.catalogue.results['matches'],
            16,
            'Expected 16 records against ISO typename')

    def test_csw_outputschema_dc(self):
        """Verify that GeoNode CSW can handle ISO metadata with Dublin Core outputSchema"""

        csw = get_catalogue()

        # search for 'san_andres_y_providencia_location', output as Dublin Core
        csw.catalogue.getrecords(
            typenames='gmd:MD_Metadata',
            keywords=['%san_andres_y_providencia_location%'],
            outputschema='http://www.opengis.net/cat/csw/2.0.2',
            esn='full')

        record = csw.catalogue.records.values()[0]

        # test that the ISO title maps correctly in Dublin Core
        self.assertEqual(record.title, 'San Andres Y Providencia Location',
                         'Expected a specific title in Dublin Core model')

        # test that the ISO abstract maps correctly in Dublin Core
        self.assertEqual(record.abstract, 'No abstract provided',
                         'Expected a specific abstract in Dublin Core model')

        # test for correct service link articulation
        for link in record.references:
            if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                if link['scheme'] == 'OGC:WMS':
                    self.assertEqual(
                        link['url'],
                        'http://localhost:8080/geoserver/geonode/ows',
                        'Expected a specific OGC:WMS URL')
                elif link['scheme'] == 'OGC:WFS':
                    self.assertEqual(
                        link['url'],
                        'http://localhost:8080/geoserver/geonode/wfs',
                        'Expected a specific OGC:WFS URL')
            elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
                if link['scheme'] == 'OGC:WMS':
                    self.assertEqual(
                        link['url'],
                        'http://localhost:8000/qgis-server/ogc/'
                        'san_andres_y_providencia_location',
                        'Expected a specific OGC:WMS URL')
                elif link['scheme'] == 'OGC:WFS':
                    self.assertEqual(
                        link['url'],
                        'http://localhost:8000/qgis-server/ogc/'
                        'san_andres_y_providencia_location',
                        'Expected a specific OGC:WFS URL')

    def test_csw_outputschema_iso(self):
        """Verify that GeoNode CSW can handle ISO metadata with ISO outputSchema"""

        csw = get_catalogue()

        # search for 'san_andres_y_providencia_location', output as Dublin Core
        csw.catalogue.getrecords(
            typenames='gmd:MD_Metadata',
            keywords=['%san_andres_y_providencia_location%'],
            outputschema='http://www.isotc211.org/2005/gmd',
            esn='full')

        record = csw.catalogue.records.values()[0]

        # test that the ISO title maps correctly in Dublin Core
        self.assertEqual(
            record.identification.title,
            'San Andres Y Providencia Location',
            'Expected a specific title in ISO model')

        # test that the ISO abstract maps correctly in Dublin Core
        self.assertEqual(
            record.identification.abstract,
            'No abstract provided',
            'Expected a specific abstract in ISO model')

        # test BBOX properties in Dublin Core
        from decimal import Decimal
        self.assertEqual(
            Decimal(record.identification.bbox.minx),
            Decimal('-81.8593555'),
            'Expected a specific minx coordinate value in ISO model')
        self.assertEqual(
            Decimal(record.identification.bbox.miny),
            Decimal('12.1665322'),
            'Expected a specific minx coordinate value in ISO model')
        self.assertEqual(
            Decimal(record.identification.bbox.maxx),
            Decimal('-81.356409'),
            'Expected a specific maxx coordinate value in ISO model')
        self.assertEqual(
            Decimal(record.identification.bbox.maxy),
            Decimal('13.396306'),
            'Expected a specific maxy coordinate value in ISO model')

        # test for correct link articulation
        for link in record.distribution.online:
            if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                if link.protocol == 'OGC:WMS':
                    self.assertEqual(
                        link.url,
                        'http://localhost:8080/geoserver/geonode/ows',
                        'Expected a specific OGC:WMS URL')
                elif link.protocol == 'OGC:WFS':
                    self.assertEqual(
                        link.url,
                        'http://localhost:8080/geoserver/geonode/wfs',
                        'Expected a specific OGC:WFS URL')
            if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
                if link.protocol == 'OGC:WMS':
                    self.assertEqual(
                        link.url,
                        'http://localhost:8000/qgis-server/ogc/'
                        'san_andres_y_providencia_location',
                        'Expected a specific OGC:WMS URL')
                elif link.protocol == 'OGC:WFS':
                    self.assertEqual(
                        link.url,
                        'http://localhost:8000/qgis-server/ogc/'
                        'san_andres_y_providencia_location',
                        'Expected a specific OGC:WFS URL')

    def test_csw_outputschema_dc_bbox(self):
        """Verify that GeoNode CSW can handle ISO metadata BBOX model with Dublin Core outputSchema"""

        # GeoNetwork is not to spec for DC BBOX output
        # once ticket http://trac.osgeo.org/geonetwork/ticket/730 is fixed
        # we can remove this condition

        csw = get_catalogue()
        if csw.catalogue.type != 'geonetwork':
            # search for 'san_andres_y_providencia_location', output as Dublin
            # Core
            csw.catalogue.getrecords(
                typenames='gmd:MD_Metadata',
                keywords=['san_andres_y_providencia_location'],
                outputschema='http://www.opengis.net/cat/csw/2.0.2',
                esn='full')

            record = csw.catalogue.records.values()[0]

            # test CRS constructs in Dublin Core
            self.assertEqual(
                record.bbox.crs.code,
                4326,
                'Expected a specific CRS code value in Dublin Core model')
            # test BBOX properties in Dublin Core
            from decimal import Decimal
            logger.debug([Decimal(record.bbox.minx), Decimal(record.bbox.miny),
                         Decimal(record.bbox.maxx), Decimal(record.bbox.maxy)])
            self.assertEqual(
                Decimal(record.bbox.minx),
                Decimal('-81.8593555'),
                'Expected a specific minx coordinate value in Dublin Core model')
            self.assertEqual(
                Decimal(record.bbox.miny),
                Decimal('12.1665322'),
                'Expected a specific minx coordinate value in Dublin Core model')
            self.assertEqual(
                Decimal(record.bbox.maxx),
                Decimal('-81.356409'),
                'Expected a specific maxx coordinate value in Dublin Core model')
            self.assertEqual(
                Decimal(record.bbox.maxy),
                Decimal('13.396306'),
                'Expected a specific maxy coordinate value in Dublin Core model')

    def test_csw_outputschema_fgdc(self):
        """Verify that GeoNode CSW can handle ISO metadata with FGDC outputSchema"""

        # GeoNetwork and deegree do not transform ISO <-> FGDC
        # once this is implemented we can remove this condition

        csw = get_catalogue()
        if csw.catalogue.type in ['pycsw_http', 'pycsw_local']:
            # get all ISO records in FGDC schema
            csw.catalogue.getrecords(
                typenames='gmd:MD_Metadata',
                keywords=['san_andres_y_providencia_location'],
                outputschema='http://www.opengis.net/cat/csw/csdgm')

            record = csw.catalogue.records.values()[0]

            # test that the ISO title maps correctly in FGDC
            self.assertEqual(
                record.idinfo.citation.citeinfo['title'],
                'San Andres Y Providencia Location',
                'Expected a specific title in FGDC model')

            # test that the ISO abstract maps correctly in FGDC
            self.assertEqual(
                record.idinfo.descript.abstract,
                'No abstract provided',
                'Expected a specific abstract in FGDC model')

    def test_csw_query_bbox(self):
        """Verify that GeoNode CSW can handle bbox queries"""

        csw = get_catalogue()
        csw.catalogue.getrecords(bbox=[-140, -70, 80, 70])
        logger.debug(csw.catalogue.results)
        self.assertEqual(
            csw.catalogue.results,
            {'matches': 7, 'nextrecord': 0, 'returned': 7},
            'Expected a specific bbox query result set')

    def test_csw_upload_fgdc(self):
        """Verify that GeoNode CSW can handle FGDC metadata upload"""

        # GeoNetwork and deegree do not transform ISO <-> FGDC
        # once this is implemented we can remove this condition

        csw = get_catalogue()
        if csw.catalogue.type == 'pycsw_http':
            # upload a native FGDC metadata document
            md_doc = etree.tostring(
                etree.fromstring(
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
            self.assertEqual(
                csw.catalogue.results['inserted'],
                1,
                'Expected 1 inserted record in FGDC model')

            # query against FGDC typename, output FGDC
            csw.catalogue.getrecords(typenames='fgdc:metadata')
            self.assertEqual(
                csw.catalogue.results['matches'],
                1,
                'Expected 1 record in FGDC model')

            record = csw.catalogue.records.values()[0]

            # test that the FGDC title maps correctly in DC
            self.assertEqual(
                record.title,
                'Census_Blockgroup_Pop_Housing',
                'Expected a specific title in DC model')

            # test that the FGDC type maps correctly in DC
            self.assertEqual(
                record.type,
                'vector digital data',
                'Expected a specific type in DC model')

            # test CRS constructs in Dublin Core
            self.assertEqual(
                record.bbox.crs.code,
                4326,
                'Expected a specific CRS code value in Dublin Core model')

            # test BBOX properties in Dublin Core
            from decimal import Decimal
            self.assertEqual(
                Decimal(record.bbox.minx),
                Decimal('-117.6'),
                'Expected a specific minx coordinate value in Dublin Core model')
            self.assertEqual(
                Decimal(record.bbox.miny),
                Decimal('32.53'),
                'Expected a specific minx coordinate value in Dublin Core model')
            self.assertEqual(
                Decimal(record.bbox.maxx),
                Decimal('-116.08'),
                'Expected a specific maxx coordinate value in Dublin Core model')
            self.assertEqual(
                Decimal(record.bbox.maxy),
                Decimal('33.51'),
                'Expected a specific maxy coordinate value in Dublin Core model')

            # query against FGDC typename, return in ISO
            csw.catalogue.getrecords(
                typenames='fgdc:metadata',
                esn='brief',
                outputschema='http://www.isotc211.org/2005/gmd')
            self.assertEqual(
                csw.catalogue.results['matches'],
                1,
                'Expected 1 record in ISO model')

            record = csw.catalogue.records.values()[0]

            # test that the FGDC title maps correctly in ISO
            self.assertEqual(
                record.identification.title,
                'Census_Blockgroup_Pop_Housing',
                'Expected a specific title in ISO model')

            # cleanup and delete inserted FGDC metadata document
            csw.catalogue.transaction(
                ttype='delete',
                typename='fgdc:metadata',
                cql='fgdc:Title like "Census_Blockgroup_Pop_Housing"')
            self.assertEqual(
                csw.catalogue.results['deleted'],
                1,
                'Expected 1 deleted record in FGDC model')

    def test_csw_bulk_upload(self):
        """Verify that GeoNode CSW can handle bulk upload of ISO and FGDC metadata"""

        # GeoNetwork and deegree do not transform ISO <-> FGDC
        # once this is implemented we can remove this condition

        csw = get_catalogue()
        if csw.catalogue.type == 'pycsw_http':

            identifiers = []

            # upload all metadata
            for root, dirs, files in os.walk(os.path.join(gisdata.GOOD_METADATA, 'sangis.org')):
                for mfile in files:
                    if mfile.endswith('.xml'):
                        md_doc = etree.tostring(
                            etree.fromstring(
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
                md_doc = etree.tostring(etree.fromstring(open(md).read()))
                csw.catalogue.transaction(
                    ttype='insert',
                    typename='gmd:MD_Metadata',
                    record=md_doc)
                identifiers.append(csw.catalogue.results['insertresults'][0])

            # query against FGDC typename
            csw.catalogue.getrecords(typenames='fgdc:metadata')
            self.assertEqual(
                csw.catalogue.results['matches'],
                72,
                'Expected 187 records in FGDC model')

            # query against ISO typename
            csw.catalogue.getrecords(typenames='gmd:MD_Metadata')
            self.assertEqual(
                csw.catalogue.results['matches'],
                115,
                'Expected 194 records in ISO model')

            # query against FGDC and ISO typename
            csw.catalogue.getrecords(typenames='gmd:MD_Metadata fgdc:metadata')
            self.assertEqual(
                csw.catalogue.results['matches'],
                187,
                'Expected 381 records total in FGDC and ISO model')

            # clean up
            for i in identifiers:
                csw.catalogue.transaction(ttype='delete', identifier=i)


#    def test_layer_delete_from_catalogue(self):
#        """Verify that layer is correctly deleted from Catalogue
#        """
#
# Test Uploading then Deleting a Shapefile from Catalogue
#        shp_file = os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp')
#        shp_layer = file_upload(shp_file)
#        catalogue = get_catalogue()
#        catalogue.remove_record(shp_layer.uuid)
#        shp_layer_info = catalogue.get_record(shp_layer.uuid)
#        self.assertEqual(shp_layer_info, None, 'Expected no layer info for Shapefile')
#
# Clean up and completely delete the layer
#        shp_layer.delete()
#
# Test Uploading then Deleting a TIFF file from GeoNetwork
#        tif_file = os.path.join(gisdata.RASTER_DATA, 'test_grid.tif')
#        tif_layer = file_upload(tif_file)
#        catalogue.remove_record(tif_layer.uuid)
#        tif_layer_info = catalogue.get_record(tif_layer.uuid)
#        self.assertEqual(tif_layer_info, None, 'Expected no layer info for TIFF file')
#
# Clean up and completely delete the layer
#        tif_layer.delete()
