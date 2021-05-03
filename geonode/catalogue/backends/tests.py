import ast
from django.test.utils import override_settings
from owslib.etree import etree
from geonode.base.populate_test_data import create_single_doc, create_single_layer, create_single_map
from django.contrib.auth.models import AnonymousUser
from django.test.client import RequestFactory
from geonode.catalogue.views import csw_global_dispatch
from django.test import TestCase
from django.conf import settings

pycsw_settings = settings.PYCSW.copy()
pycsw_settings_all = settings.PYCSW.copy()
pycsw_settings['FILTER'] = {'resource_type__in': ['layer', 'map']}
pycsw_settings_all['FILTER'] = {'resource_type__in': ['layer', 'map', 'document']}


class TestGeoNodeRepository(TestCase):
    # to simplify the tests we pass throught csw_global_dispatch
    # since call the GeoNodeRepository.query
    def setUp(self):
        self.layer = create_single_layer("layer_name")
        self.map = create_single_map("map_name")
        self.doc = create_single_doc("doc_name")
        self.request = self.__request_factory()

    def test_if_pycsw_filter_is_not_set_should_return_only_the_layer_by_default(self):
        response = csw_global_dispatch(self.request)
        root = etree.fromstring(response.content)
        child = [x.attrib for x in root.getchildren() if 'numberOfRecordsMatched' in x.attrib]
        returned_results = ast.literal_eval(child[0].get('numberOfRecordsMatched', '0')) if child else 0
        self.assertEqual(1, returned_results)

    @override_settings(PYCSW=pycsw_settings)
    def test_if_pycsw_filter_is_set_should_return_only_layers_and_map(self):
        response = csw_global_dispatch(self.request)
        root = etree.fromstring(response.content)
        child = [x.attrib for x in root.getchildren() if 'numberOfRecordsMatched' in x.attrib]
        returned_results = ast.literal_eval(child[0].get('numberOfRecordsMatched', '0')) if child else 0
        self.assertEqual(2, returned_results)

    @override_settings(PYCSW=pycsw_settings_all)
    def test_if_pycsw_filter_is_set_should_return_all_layers_map_doc(self):
        response = csw_global_dispatch(self.request)
        root = etree.fromstring(response.content)
        child = [x.attrib for x in root.getchildren() if 'numberOfRecordsMatched' in x.attrib]
        returned_results = ast.literal_eval(child[0].get('numberOfRecordsMatched', '0')) if child else 0
        self.assertEqual(3, returned_results)

    @staticmethod
    def __request_factory():
        factory = RequestFactory()
        url = "http://localhost:8000/catalogue/csw?request=GetRecords"
        url += "&service=CSW&version=2.0.2&outputschema=http%3A%2F%2Fwww.isotc211.org%2F2005%2Fgmd"
        url += "&elementsetname=brief&typenames=csw:Record&resultType=results"
        request = factory.get(url)

        request.user = AnonymousUser()
        return request
