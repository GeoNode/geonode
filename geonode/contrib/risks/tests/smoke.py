# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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
import traceback
import StringIO

from django.db import connections
from django.core.management import call_command

from geonode.layers.models import Layer
from geonode.contrib.risks.models import Region
from geonode.contrib.risks.models import RiskAnalysis, HazardType
from geonode.contrib.risks.models import AnalysisType, DymensionInfo
from geonode.contrib.risks.models import RiskAnalysisDymensionInfoAssociation
from geonode.contrib.risks.tests import RisksTestCase

TESTDATA_FILE_INI = os.path.join(
    os.path.dirname(__file__),
    'resources/impact_analysis_results_test.ini')

TESTDATA_FILE_DATA = os.path.join(
    os.path.dirname(__file__),
    'resources/impact_analysis_results_test.xlsx')

TEST_HAZARD_TYPE = 'EQ'
TEST_ANALYSIS_TYPE = 'impact'
TEST_GS_LAYER = 'test'
TEST_RISK_ANALYSIS = 'WP6_future_proj_Hospital'
TEST_REGION = 'Afghanistan'

TEST_DIM_1 = 'Scenario'
TEST_DIM_2 = 'Round Period'

PDF_INPUT_TEST = os.path.join(
    os.path.dirname(__file__),
    'resources', 'pdf_input_test.jpg')


class RisksSmokeTests(RisksTestCase):
    """
    To run the tests

      python manage.py test geonode.contrib.risks.tests.smoke

    """

    def setUp(self):
        # Test initialization
        RisksTestCase.setUp(self)

        # Sanity Checks
        self.assertTrue(os.path.isfile(TESTDATA_FILE_INI))
        self.assertTrue(os.path.isfile(TESTDATA_FILE_DATA))

    def tearDown(self):
        # Test deinit
        RisksTestCase.tearDown(self)

    def _TestCreateRiskAnalysis(self):
        """Test creation of new Risk Analysis definitions"""
        try:
            hazard = HazardType.objects.get(mnemonic=TEST_HAZARD_TYPE)
            self.assertIsNotNone(hazard)

            analysis = AnalysisType.objects.get(name=TEST_ANALYSIS_TYPE)
            self.assertIsNotNone(analysis)

            layer = Layer.objects.get(name=TEST_GS_LAYER)
            self.assertIsNotNone(layer)
        except:
            traceback.print_exc()
            self.assertTrue(False)

        out = StringIO.StringIO()
        """
        Example:

            createriskanalysis \
                    -f WP6__Impact_analysis_results_future_projections_Hospital.ini
        """
        call_command('createriskanalysis', descriptor_file=TESTDATA_FILE_INI, stdout=out)
        value = out.getvalue()
        try:
            risk = RiskAnalysis.objects.get(name=str(value).strip())
            self.assertIsNotNone(risk)

            dim1 = DymensionInfo.objects.get(name=TEST_DIM_1)
            self.assertIsNotNone(dim1)

            dim2 = DymensionInfo.objects.get(name=TEST_DIM_2)
            self.assertIsNotNone(dim2)

            rd1 = RiskAnalysisDymensionInfoAssociation.objects.filter(dymensioninfo=dim1, riskanalysis=risk)
            self.assertIsNotNone(rd1)
            self.assertEqual(len(rd1), 2)
            self.assertEqual(rd1[0].order, 0)
            self.assertEqual(rd1[0].axis, u'x')
            self.assertEqual(rd1[0].value, u'Hospital')
            self.assertEqual(rd1[1].order, 1)
            self.assertEqual(rd1[1].axis, u'x')
            self.assertEqual(rd1[1].value, u'SSP1')

            rd2 = RiskAnalysisDymensionInfoAssociation.objects.filter(dymensioninfo=dim2, riskanalysis=risk)
            self.assertIsNotNone(rd2)
            self.assertEqual(len(rd2), 2)
            self.assertEqual(rd2[0].order, 0)
            self.assertEqual(rd2[0].axis, u'y')
            self.assertEqual(rd2[0].value, u'10')
            self.assertEqual(rd2[1].order, 1)
            self.assertEqual(rd2[1].axis, u'y')
            self.assertEqual(rd2[1].value, u'20')
        except:
            traceback.print_exc()
            self.assertTrue(False)

    def _TestImportRiskAnalysisData(self):
        """Test creation of new Risk Analysis definitions"""
        try:
            hazard = HazardType.objects.get(mnemonic=TEST_HAZARD_TYPE)
            self.assertIsNotNone(hazard)

            analysis = AnalysisType.objects.get(name=TEST_ANALYSIS_TYPE)
            self.assertIsNotNone(analysis)

            layer = Layer.objects.get(name=TEST_GS_LAYER)
            self.assertIsNotNone(layer)

            risk = RiskAnalysis.objects.get(name=TEST_RISK_ANALYSIS)
            self.assertIsNotNone(risk)

            region = Region.objects.get(name=TEST_REGION)
            self.assertIsNotNone(region)
        except:
            traceback.print_exc()
            self.assertTrue(False)

        out = StringIO.StringIO()
        """
        Example:

            importriskdata -r Afghanistan -k "WP6_future_proj_Population" \
                            -x WP6__Impact_analysis_results_future_projections_Population.xlsx
        """
        call_command(
            'importriskdata',
            commit=True,
            excel_file=TESTDATA_FILE_DATA,
            region=TEST_REGION,
            risk_analysis=TEST_RISK_ANALYSIS,
            stdout=out)

        value1 = None
        with connections['datastore'].cursor() as cursor:
            cursor.execute('SELECT count(test_fid) FROM public.test_dimensions;')
            self.assertFalse(cursor.rowcount == 0)

            value1 = cursor.fetchone()

        # Execute twice and check that we don't have duplicates
        call_command(
            'importriskdata',
            commit=True,
            excel_file=TESTDATA_FILE_DATA,
            region=TEST_REGION,
            risk_analysis=TEST_RISK_ANALYSIS,
            stdout=out)

        value2 = None
        with connections['datastore'].cursor() as cursor:
            cursor.execute('SELECT count(test_fid) FROM public.test_dimensions;')
            self.assertFalse(cursor.rowcount == 0)

            value2 = cursor.fetchone()

        self.assertIsNotNone(value1)
        self.assertIsNotNone(value2)
        self.assertEqual(value1, value2)

    def test_smoke_createanalysis(self):
        """
        Execute smoke tests in a predefined order
        """
        self._TestCreateRiskAnalysis()
        self._TestImportRiskAnalysisData()
