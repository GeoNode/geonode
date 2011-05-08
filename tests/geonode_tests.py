import os
from django.conf import settings
from django.test import TestCase

from geonode.maps.utils import *

from geonode.maps.gs_helpers import cascading_delete, fixup_style

from django.core.exceptions import ObjectDoesNotExist

TEST_DATA = os.path.join(settings.PROJECT_ROOT, 'geonode_test_data')

class GeoNodeCoreTest(TestCase):
    """Tests geonode.core app/module
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_something(self):
        assert(True)
    
class GeoNodeProxyTest(TestCase):
    """Tests geonode.proxy app/module
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_something(self):
        assert(True)

class GeoNodeMapTest(TestCase):
    """Tests geonode.maps app/module
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_something(self):
        assert(True)

    # geonode.maps.models

    def test_layer_delete_from_geoserver(self):
        """Verify that layer is correctly deleted from GeoServer
        """
        # Layer.delete_from_geoserver() uses cascading_delete()
        # Should we explicitly test that the styles and store are
        # deleted as well as the resource itself?
        # There is already an explicit test for cascading delete

        gs_cat = Layer.objects.gs_catalog

        # Test Uploading then Deleting a Shapefile from GeoServer
        shp_file = os.path.join(TEST_DATA, 'lembang_schools.shp')
        shp_layer = file_upload(shp_file)
        shp_store = gs_cat.get_store(shp_layer.name)
        shp_layer.delete_from_geoserver()
        self.assertRaises(FailedRequestError,
            lambda: gs_cat.get_resource(shp_layer.name, store=shp_store))

        shp_layer.delete()

        # Test Uploading then Deleting a TIFF file from GeoServer
        tif_file = os.path.join(TEST_DATA, 'test_grid.tif')
        tif_layer = file_upload(tif_file)
        tif_store = gs_cat.get_store(tif_layer.name)
        tif_layer.delete_from_geoserver()
        self.assertRaises(FailedRequestError,
            lambda: gs_cat.get_resource(shp_layer.name, store=tif_store))

        tif_layer.delete()

    def test_layer_delete_from_geonetwork(self):
        """Verify that layer is correctly deleted from GeoNetwork
        """

        gn_cat = Layer.objects.gn_catalog

        # Test Uploading then Deleting a Shapefile from GeoNetwork
        shp_file = os.path.join(TEST_DATA, 'lembang_schools.shp')
        shp_layer = file_upload(shp_file)
        shp_layer.delete_from_geonetwork()
        shp_layer_info = gn_cat.get_by_uuid(shp_layer.uuid)
        assert shp_layer_info == None

        # Clean up and completely delete the layer
        shp_layer.delete()

        # Test Uploading then Deleting a TIFF file from GeoNetwork
        tif_file = os.path.join(TEST_DATA, 'test_grid.tif')
        tif_layer = file_upload(tif_file)
        tif_layer.delete_from_geonetwork()
        tif_layer_info = gn_cat.get_by_uuid(tif_layer.uuid)
        assert tif_layer_info == None

        # Clean up and completely delete the layer
        tif_layer.delete()

    def test_delete_layer(self):
        """Verify that the 'delete_layer' pre_delete hook is functioning
        """

        gs_cat = Layer.objects.gs_catalog
        gn_cat = Layer.objects.gn_catalog

        # Upload a Shapefile Layer
        shp_file = os.path.join(TEST_DATA, 'lembang_schools.shp')
        shp_layer = file_upload(shp_file)
        shp_layer_id = shp_layer.pk
        shp_store = gs_cat.get_store(shp_layer.name)
        shp_store_name = shp_store.name

        id = shp_layer.pk
        name = shp_layer.name
        uuid = shp_layer.uuid

        # Delete it with the Layer.delete() method
        shp_layer.delete()

        # Verify that it no longer exists in GeoServer
        self.assertRaises(FailedRequestError,
            lambda: gs_cat.get_resource(name, store=shp_store))
        self.assertRaises(FailedRequestError,
            lambda: gs_cat.get_store(shp_store_name))

        # Verify that it no longer exists in GeoNetwork
        shp_layer_gn_info = gn_cat.get_by_uuid(uuid)
        assert shp_layer_gn_info == None

        # Check that it was also deleted from GeoNodes DB
        self.assertRaises(ObjectDoesNotExist,
            lambda: Layer.objects.get(pk=shp_layer_id))

    # geonode.maps.gs_helpers

    def test_cascading_delete(self):
        """Verify that the gs_helpers.cascading_delete() method is working properly
        """
        gs_cat = Layer.objects.gs_catalog

        # Upload a Shapefile
        shp_file = os.path.join(TEST_DATA, 'lembang_schools.shp')
        shp_layer = file_upload(shp_file)
       
        # Save the names of the Resource/Store/Styles 
        resource_name = shp_layer.resource.name
        store = shp_layer.resource.store
        store_name = store.name
        layer = gs_cat.get_layer(resource_name)
        styles = layer.styles + [layer.default_style]
        
        # Delete the Layer using cascading_delete()
        cascading_delete(gs_cat, shp_layer.resource)
        
        # Verify that the styles were deleted
        for style in styles:
            s = gs_cat.get_style(style)
            assert s == None
        
        # Verify that the resource was deleted
        self.assertRaises(FailedRequestError, lambda: gs_cat.get_resource(resource_name, store=store))

        # Verify that the store was deleted 
        self.assertRaises(FailedRequestError, lambda: gs_cat.get_store(store_name))

        # Clean up by deleting the layer from GeoNode's DB and GeoNetwork
        shp_layer.delete()
