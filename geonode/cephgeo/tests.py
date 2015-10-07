from django.test import TestCase
from django.http import HttpRequest

from geonode import settings
from changuito import CartProxy
from changuito import models as cartmodels

import geonode.cephgeo.models
import geonode.cephgeo.utils
import geonode.layers.models
import random

class UtilsTestCase(TestCase):
    
    fixtures = ['bobby']
    
    def setUp(self, username):
        self.user = get_user_model().objects.get_or_create(username=username, is_superuser=True)
        self.password = 'genericsemistrongpassword'
        self.anonymous_user = get_anonymous_user()
        self.cart= 
        self.item_list = []
        
        r = HttpRequest()
        r.session = {}
        r.user = self.user
        self.request =r
        
    
    def _setup_cart(self, numberOfItems):
        self.item_list = random.sample(CephDataObject.objects.all(), numberOfItems)
        
        for x in item_list:
            self.cart.add(x, 1, 1)
        
        
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
        
        self.assertEqual(is_valid_grid_ref(test1), True)
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
        self. _setup_cart(5)
        item_list_tot_size = 0
        for x in self.item_list:
            item_list_tot_size += x.size_in_bytes

        self.assertEqual(get_cart_datasize(self.request), item_list_tot_size)
        
        
    
