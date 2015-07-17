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
import math
from django.test import TestCase
from django.core.urlresolvers import reverse

from geonode.utils import forward_mercator, inverse_mercator


class GeoNodeSmokeTests(TestCase):

    fixtures = ['people_data.json']
    GEOSERVER = False

    def setUp(self):
        # If Geoserver and GeoNetwork are not running
        # avoid running tests that call those views.
        if "GEOSERVER" in os.environ.keys():
            self.GEOSERVER = True

    def tearDown(self):
        pass

    # Basic Pages #

    def test_home_page(self):
        '''Test if the homepage renders.'''
        response = self.client.get(reverse('home'))
        self.failUnlessEqual(response.status_code, 200)

    def test_help_page(self):
        '''Test help page renders.'''

        response = self.client.get(reverse('help'))
        self.failUnlessEqual(response.status_code, 200)

    def test_developer_page(self):
        '''Test help page renders.'''

        response = self.client.get(reverse('help'))
        self.failUnlessEqual(response.status_code, 200)

    # Layer Pages #

    def test_layer_page(self):
        'Test if the data home page renders.'
        response = self.client.get(reverse('layer_browse'))
        self.failUnlessEqual(response.status_code, 200)

    def test_layer_acls(self):
        'Test if the data/acls endpoint renders.'
        response = self.client.get(reverse('layer_acls'))
        self.failUnlessEqual(response.status_code, 200)

    # Maps Pages #

    def test_maps_page(self):
        '''Test Maps page renders.'''

        response = self.client.get(reverse('maps_browse'))
        self.failUnlessEqual(response.status_code, 200)

    def test_new_map_page(self):
        '''Test New Map page renders.'''

        response = self.client.get(reverse('new_map'))
        self.failUnlessEqual(response.status_code, 200)

    # People Pages #

    def test_profile_list(self):
        '''Test the profiles page renders.'''

        response = self.client.get(reverse('profile_browse'))
        self.failUnlessEqual(response.status_code, 200)

    def test_profiles(self):
        '''Test that user profile pages render.'''
        response = self.client.get(reverse('profile_detail', args=['admin']))
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get(reverse('profile_detail', args=['norman']))
        self.failUnlessEqual(response.status_code, 200)

    def test_csw_endpoint(self):
        '''Test that the CSW endpoint is correctly configured.'''
        response = self.client.get(reverse('csw_global_dispatch'))
        self.failUnlessEqual(response.status_code, 200)

    def test_opensearch_description(self):
        '''Test that the local OpenSearch endpoint is correctly configured.'''
        response = self.client.get(reverse('opensearch_dispatch'))
        self.failUnlessEqual(response.status_code, 200)


class GeoNodeUtilsTests(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # Some other Stuff

    """
    def test_check_geonode_is_up(self):
        from contextlib import nested
        from geonode.utils import check_geonode_is_up

        def blowup():
            raise Exception("BOOM")

        with patch('geonode.maps.models.gs_catalog') as mock_gs:
            mock_gs.get_workspaces.side_effect = blowup

            self.assertRaises(GeoNodeException, check_geonode_is_up)

        with nested(
            patch('geonode.maps.models.gs_catalog'),
            patch('geonode.maps.models.Layer.objects.geonetwork')
        ) as (mock_gs, mock_gn):
            mock_gn.login.side_effect = blowup
            self.assertRaises(GeoNodeException, check_geonode_is_up)
            self.assertTrue(mock_gs.get_workspaces.called)

        with nested(
            patch('geonode.maps.models.gs_catalog'),
            patch('geonode.maps.models.Layer.objects.geonetwork')
        ) as (mock_gs, mock_gn):
            # no assertion, this should just run without error
            check_geonode_is_up()
    """

    def test_forward_mercator(self):
        arctic = forward_mercator((0, 85))
        antarctic = forward_mercator((0, -85))
        hawaii = forward_mercator((-180, 0))
        phillipines = forward_mercator((180, 0))
        ne = forward_mercator((180, 90))
        sw = forward_mercator((-180, -90))

        inf_test = forward_mercator(
            (-8.988465674311579e+307, -8.988465674311579e+307)
        )

        self.assertEqual(inf_test[0], float('-inf'))
        self.assertEqual(inf_test[1], float('-inf'))

        self.assertEqual(round(arctic[0]), 0, "Arctic longitude is correct")
        self.assertEqual(
            round(
                arctic[1]),
            19971869,
            "Arctic latitude is correct")

        self.assertEqual(
            round(
                antarctic[0]),
            0,
            "Antarctic longitude is correct")
        self.assertEqual(
            round(
                antarctic[1]), -19971869, "Antarctic latitude is correct")

        self.assertEqual(
            round(
                hawaii[0]), -20037508, "Hawaiian lon is correct")
        self.assertEqual(round(hawaii[1]), 0, "Hawaiian lat is correct")

        self.assertEqual(
            round(
                phillipines[0]),
            20037508,
            "Phillipines lon is correct")
        self.assertEqual(
            round(
                phillipines[1]),
            0,
            "Phillipines lat is correct")

        self.assertEqual(round(ne[0]), 20037508, "NE lon is correct")
        self.assertTrue(ne[1] > 50000000, "NE lat is correct")

        self.assertEqual(round(sw[0]), -20037508, "SW lon is correct")
        self.assertTrue(math.isinf(sw[1]), "SW lat is correct")

        # verify behavior for invalid y values
        self.assertEqual(float('-inf'), forward_mercator((0, 135))[1])
        self.assertEqual(float('-inf'), forward_mercator((0, -135))[1])

    def test_inverse_mercator(self):
        arctic = inverse_mercator(forward_mercator((0, 85)))
        antarctic = inverse_mercator(forward_mercator((0, -85)))
        hawaii = inverse_mercator(forward_mercator((-180, 0)))
        phillipines = inverse_mercator(forward_mercator((180, 0)))
        ne = inverse_mercator(forward_mercator((180, 90)))
        sw = inverse_mercator(forward_mercator((-180, -90)))

        self.assertAlmostEqual(
            arctic[0],
            0.0,
            msg="Arctic longitude is correct")
        self.assertAlmostEqual(
            arctic[1],
            85.0,
            msg="Arctic latitude is correct")

        self.assertAlmostEqual(
            antarctic[0],
            0.0,
            msg="Antarctic longitude is correct")
        self.assertAlmostEqual(
            antarctic[1], -85.0, msg="Antarctic latitude is correct")

        self.assertAlmostEqual(
            hawaii[0], -180.0, msg="Hawaiian lon is correct")
        self.assertAlmostEqual(hawaii[1], 0.0, msg="Hawaiian lat is correct")

        self.assertAlmostEqual(
            phillipines[0],
            180.0,
            msg="Phillipines lon is correct")
        self.assertAlmostEqual(
            phillipines[1],
            0.0,
            msg="Phillipines lat is correct")

        self.assertAlmostEqual(ne[0], 180.0, msg="NE lon is correct")
        self.assertAlmostEqual(ne[1], 90.0, msg="NE lat is correct")

        self.assertAlmostEqual(sw[0], -180.0, msg="SW lon is correct")
        self.assertAlmostEqual(sw[1], -90.0, msg="SW lat is correct")

    def test_split_query(self):
        query = 'alpha "beta gamma"   delta  '
        from geonode.utils import _split_query
        keywords = _split_query(query)
        self.assertEqual(keywords[0], "alpha")
        self.assertEqual(keywords[1], "beta gamma")
        self.assertEqual(keywords[2], "delta")


class PermissionViewTests(TestCase):
    pass
