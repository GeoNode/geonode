# -*- coding: utf-8 -*-
from django.test import SimpleTestCase
from django.contrib.gis.gdal import SpatialReference

from gis_tools import crs_parameters


class GisTools(SimpleTestCase):

    def test_crs_parameters(self):
        """Test if can set correctly the projection for the QGIS template."""

        expected = {
            'authid': u'EPSG:4326',
            'description': u'WGS 84',
            'ellipsoide_acronym': u'WGS84',
            'geogcs': u'WGS 84',
            'geographic': u'True',
            'proj4': u'+proj=longlat +datum=WGS84 +no_defs ',
            'projection_acronym': u'longlat',
            'srid': u'4326',
            'srsid': u'3452',
            'units': u'degree'
        }
        self.assertEqual(crs_parameters(SpatialReference(4326)), expected)

        expected = {
            'authid': u'EPSG:3857',
            'description': u'WGS 84 / Pseudo Mercator',
            'ellipsoide_acronym': u'WGS84',
            'geogcs': u'WGS 84',
            'geographic': u'False',
            'proj4': u'+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 '
                     u'+lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m '
                     u'+nadgrids=@null +wktext  +no_defs',
            'projection_acronym': u'merc',
            'srid': u'3857',
            'srsid': u'3857',
            'units': u'meters'
        }
        self.assertEqual(crs_parameters(SpatialReference(3857)), expected)
