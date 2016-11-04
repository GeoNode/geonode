from django.test import TestCase
from django.http import HttpRequest

from django.conf import settings
from changuito import CartProxy
from changuito import models as cartmodels

from django.contrib.auth import get_user_model
from geonode.base.populate_test_data import create_models
from guardian.shortcuts import get_anonymous_user

from pprint import pprint

import geonode.cephgeo.models
from geonode.cephgeo.utils import *
import geonode.layers.models
import random

class UtilsTestCase(TestCase):
    
    fixtures = ['bobby']
    comodel = ("NAME","LAST_MODIFIED","SIZE_IN_BYTES","CONTENT_TYPE","GEO_TYPE","FILE_HASH","GRID_REF")
    cephobjects = [
        ("E240N1782_ORTHO.tif","2015-06-25 15:36:24","12000344","image/tiff","","cdcfb5297fea40a067ea8b50351205a7","E240N1782"),
        ("E211N1749_ORTHO.tif","2015-06-25 15:36:25","12000344","image/tiff","","c8fcf62ce2f0a9f84e28a8d93eb82b3c","E211N1749"),
        ("E233N1748_ORTHO.tif","2015-06-25 15:36:26","12000344","image/tiff","","d4d147cbe294dfabdb4b1c5785e3523b","E233N1748"),
        ("E230N1752_ORTHO.tif","2015-06-25 15:36:28","12000344","image/tiff","","b9af27d72275e815a2b638c7f5d0f5b3","E230N1752"),
        ("E238N1781_ORTHO.tif","2015-06-25 15:36:29","12000344","image/tiff","","caaa4a9c7ff0ffa6a5f2c49e60fc0fee","E238N1781"),
        ("E226N1781_ORTHO.tif","2015-06-25 15:36:30","12000344","image/tiff","","baba7239ea528a9caf86238a5471e3a2","E226N1781"),
        ("E256N1751_ORTHO.tif","2015-06-25 15:36:32","12000344","image/tiff","","da02435810a3329bb7ef58710df07a4e","E256N1751"),
        ("E248N1751_ORTHO.tif","2015-06-25 15:36:33","12000344","image/tiff","","caa5482711eb7a60612e38490242d913","E248N1751"),
        ("E234N1762_ORTHO.tif","2015-06-25 15:36:34","12000344","image/tiff","","b124aadc292a889b5d7716eda524c6a7","E234N1762"),
        ("E232N1771_ORTHO.tif","2015-06-25 15:36:35","12000344","image/tiff","","053d2882a8470932425742551999a4b7","E232N1771"),
        ("E215N1779_ORTHO.tif","2015-06-25 15:36:37","12000344","image/tiff","","e70dba3321084b86045af0a1d0b4c9f7","E215N1779"),
        ("E220N1757_ORTHO.tif","2015-06-25 15:36:38","12000344","image/tiff","","8d74f2813e50de9e6f8282de5f039952","E220N1757"),
        ("E249N1768_ORTHO.tif","2015-06-25 15:36:40","12000344","image/tiff","","a806b5ade9d4a3bb55b00c5797f3b906","E249N1768"),
        ("E254N1772_ORTHO.tif","2015-06-25 15:36:41","12000344","image/tiff","","4ac1c85e1ccee7fc9d404c52d4c5a1fb","E254N1772"),
        ("E257N1768_ORTHO.tif","2015-06-25 15:36:42","12000344","image/tiff","","f3f19bb9b5dcc89118d230f3ed8a329e","E257N1768"),
        ("E252N1749_ORTHO.tif","2015-06-25 15:36:43","12000344","image/tiff","","a111de769ba0f3504674c2f14bd2c913","E252N1749"),
        ("E232N1759_ORTHO.tif","2015-06-25 15:36:45","12000344","image/tiff","","54dd45b597b2cf32558f14caad50badb","E232N1759"),
        ("E215N1751_ORTHO.tif","2015-06-25 15:36:46","12000344","image/tiff","","1083fda9188dbb16feaeb1bb7259df76","E215N1751"),
        ("E229N1750_ORTHO.tif","2015-06-25 15:36:47","12000344","image/tiff","","1d5917a4e85cfee6c5d8145c4a384858","E229N1750"),
        ("E237N1750_ORTHO.tif","2015-06-25 15:36:48","12000344","image/tiff","","e03265b08ea32cb8fc539be2e646d883","E237N1750"),
        ("E210N1758_ORTHO.tif","2015-06-25 15:36:50","12000344","image/tiff","","3982a04b64baeae0d7232c3b373055be","E210N1758"),
        ("E253N1770_ORTHO.tif","2015-06-25 15:36:51","12000344","image/tiff","","4d2c2583dd80a51f771734b3d83a17fb","E253N1770")
    ]
    
    def _populate_test_data(self):
        for o in self.cephobjects:
            cephObject = CephDataObject(
                name=o[self.comodel.index("NAME")],
                size_in_bytes= o[self.comodel.index("SIZE_IN_BYTES")],
                file_hash        = o[self.comodel.index("FILE_HASH")],
                last_modified= o[self.comodel.index("LAST_MODIFIED")], 
                 content_type= o[self.comodel.index("CONTENT_TYPE")],
                data_class     = 5,   
                grid_ref          = o[self.comodel.index("GRID_REF")]
            )
            cephObject.save()

    
    def _setup_cart(self, numberOfItems):
        self.item_list = random.sample(CephDataObject.objects.all(), numberOfItems)
        
        for x in self.item_list:
            self.cart.add(x, 1, 1)
    
    def setUp(self):
        #create_models()
        self.user = get_user_model().objects.create(username="admin",password="admin", is_superuser=True)
        pprint(self.user)
        self.password = 'admin'
        self.anonymous_user = get_anonymous_user()
        self.item_list = []
    
        r = HttpRequest()
        r.session = {}
        r.user = self.user
        
        cart = CartProxy(r)
        self.cart=cart
        self.cart_model = cart.get_cart(r)
        
        self.request = r
        self._populate_test_data()
        
    def get_data_class_from_filename_test(self):
        test1 = "name_ends_with.laz"
        test2 = "name_ends_with_dem.tif"
        test3 = "name_ends_with_dsm.tif"
        test4 = "name_ends_with_dtm.tif"
        test5 = "name_ends_with_ortho.tif"
        test6 = "name_ends_with_unmatching"
        
        self.assertEqual(get_data_class_from_filename(test1), 1)
        self.assertEqual(get_data_class_from_filename(test2), 2)
        self.assertEqual(get_data_class_from_filename(test3), 3)
        self.assertEqual(get_data_class_from_filename(test4), 4)
        self.assertEqual(get_data_class_from_filename(test5),5)
        self.assertEqual(get_data_class_from_filename(test6),0)
        
    def is_valid_grid_ref_test(self):
        test1="E1000N2000"
        test2="E100N2000"
        test3="E100N100"
        test4="E10N10"
        test5="E10000N20000"
        test6="EA1000NO2000"
        test7="EA100NO2000"
        test8="EA100NO200"
        test9="EA10NO20"
        test10="EA10000N20000"
        test11="E1000!N2000"
        test12="E1000N2000!"
        
        self.assertEqual(is_valid_grid_ref(test1), False)
        self.assertEqual(is_valid_grid_ref(test2), True)
        self.assertEqual(is_valid_grid_ref(test3), True)
        self.assertEqual(is_valid_grid_ref(test4), False)
        self.assertEqual(is_valid_grid_ref(test5), False)
        self.assertEqual(is_valid_grid_ref(test6), False)
        self.assertEqual(is_valid_grid_ref(test7), False)
        self.assertEqual(is_valid_grid_ref(test8), False)
        self.assertEqual(is_valid_grid_ref(test9), False)
        self.assertEqual(is_valid_grid_ref(test10), False)
        self.assertEqual(is_valid_grid_ref(test11), False)
        self.assertEqual(is_valid_grid_ref(test12), False)
        
    def is_valid_grid_ref_range_test(self):
        test1="E100N100-E200N200"
        test2="E100N1000-E200N2000"
        test3="E1000N100-E2000N200"
        test4="E1000N1000-E2000N2000"
        
        self.assertEqual(is_valid_grid_ref_range(test1), True)
        self.assertEqual(is_valid_grid_ref_range(test2), True)
        self.assertEqual(is_valid_grid_ref_range(test3), False)
        self.assertEqual(is_valid_grid_ref_range(test4), False)
        
    def ceph_object_id_by_data_class_test(self):
        cephObjDict =ceph_object_ids_by_data_class(CephDataObject.objects)
        
        for x in DataClassification.labels:
            for y in cephObjDict[x]:
                self.assertEqual(y.endswith(x), True)
    
    def get_cart_datasize_test(self):
        self._setup_cart(5)
        item_list_tot_size = 0.0
        for x in self.item_list:
            item_list_tot_size += x.size_in_bytes

        self.assertEqual(get_cart_datasize(self.request), item_list_tot_size)
        
        
    
