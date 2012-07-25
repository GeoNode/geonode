
from unittest import TestCase

from django.core.management import call_command

from geonode.catalogue import get_catalogue

class GeoNodeCSWTest(TestCase):
    """Tests geonode.catalogue app/module"""

    def setUp(self):
        #call_command('loaddata', 'sample_admin', verbosity=0)
        pass

    def tearDown(self):
        pass

    def test_csw_base(self):
        """Verify that GeoNode works against any CSW"""

        csw = get_catalogue(skip_caps=False)

        # test that OGC:CSW 2.0.2 is supported
        self.assertEqual(csw.catalogue.version, '2.0.2',
            'Expected "2.0.2" as a supported version')

        # test that transactions are supported
        self.assertTrue('Transaction' in [o.name for o in csw.catalogue.operations],
            'Expected Transaction to be a supported operation')

        # test that gmd:MD_Metadata is a supported typename
        for o in csw.catalogue.operations:
            if o.name == 'GetRecords':
                typenames = o.parameters['typeNames']['values']
        self.assertTrue('gmd:MD_Metadata' in typenames,
            'Expected "gmd:MD_Metadata" to be a supported typeNames value')

        # test that http://www.isotc211.org/2005/gmd is a supported outputschema
        for o in csw.catalogue.operations:
            if o.name == 'GetRecords':
                outputschemas = o.parameters['outputSchema']['values']
        self.assertTrue('http://www.isotc211.org/2005/gmd' in outputschemas,
            'Expected "http://www.isotc211.org/2005/gmd" to be a supported outputSchema value')

    def test_csw_search_count(self):
        """Verify that GeoNode can handle search counting"""

        csw = get_catalogue(skip_caps=False)

        for f in csw.catalogue.operations:
            if f.name == 'GetRecords':
                typenames = ' '.join(f.parameters['typeNames']['values'])

        # get all records
        csw.catalogue.getrecords(typenames=typenames)
        self.assertEqual(csw.catalogue.results['matches'], 10, 'Expected 10 records')

        # get all ISO records, test for numberOfRecordsMatched
        csw.catalogue.getrecords(typenames='gmd:MD_Metadata')
        self.assertEqual(csw.catalogue.results['matches'], 10, 'Expected 10 ISO records')

    def test_csw_outputschema_dc(self):
        """Verify that GeoNode can handle ISO metadata with Dublin Core outputSchema"""

        csw = get_catalogue()

        # search for 'san_andres_y_providencia_location', output as Dublin Core
        csw.catalogue.getrecords(typenames='gmd:MD_Metadata', keywords=['%san_andres_y_providencia_location%'],
            outputschema='http://www.opengis.net/cat/csw/2.0.2', esn='full')

        record = csw.catalogue.records.values()[0]

        # test that the ISO title maps correctly in Dublin Core
        self.assertEqual(record.title, 'san_andres_y_providencia_location',
            'Expected a specific title in Dublin Core model')

        # test that the ISO abstract maps correctly in Dublin Core
        self.assertEqual(record.abstract, 'No abstract provided',
            'Expected a specific abstract in Dublin Core model')

    def test_csw_outputschema_dc_bbox(self):
        """Verify that GeoNode can handle ISO metadata BBOX model with Dublin Core outputSchema"""

        # GeoNetwork is not to spec for DC BBOX output
        # once ticket http://trac.osgeo.org/geonetwork/ticket/730 is fixed
        # we can remove this condition

        csw = get_catalogue()
        if csw.catalogue.type != 'geonetwork':
            # search for 'san_andres_y_providencia_location', output as Dublin Core
            csw.catalogue.getrecords(typenames='gmd:MD_Metadata',
                keywords=['san_andres_y_providencia_location'],
                outputschema='http://www.opengis.net/cat/csw/2.0.2', esn='full')

            record = csw.catalogue.records.values()[0]

            # test CRS constructs in Dublin Core
            self.assertEqual(record.bbox.crs.code, 4326,
                'Expected a specific CRS code value in Dublin Core model')
            # test BBOX properties in Dublin Core
            self.assertEqual(record.bbox.minx, '-81.8593555',
                'Expected a specific minx coordinate value in Dublin Core model')
            self.assertEqual(record.bbox.miny, '12.1665322',
                'Expected a specific minx coordinate value in Dublin Core model')
            self.assertEqual(record.bbox.maxx, '-81.356409',
                'Expected a specific maxx coordinate value in Dublin Core model')
            self.assertEqual(record.bbox.maxy, '13.396306',
                'Expected a specific maxy coordinate value in Dublin Core model')

