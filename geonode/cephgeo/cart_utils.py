#from changuito import CartProxy
from changuito import models as cartmodels
from changuito.proxy import ItemDoesNotExist, CartProxy
from geonode.cephgeo.models import CephDataObject, DataClassification
from django.contrib import messages
import utils

class DuplicateCartItemException(Exception):
    pass

PRICING = {
	DataClassification.LAZ         : 1.00,
	DataClassification.DTM         : 1.00,
    DataClassification.DSM         : 1.00,
	DataClassification.ORTHOPHOTO  : 1.00,
    DataClassification.UNKNOWN     : 0.00,
}

def compute_price(data_class):
    try:
        return PRICING[data_class]
    except KeyError as e:
        raise KeyError("No valid pricing for geo-type [{0}]".format(data_class))

def add_to_cart(request, ceph_obj_id, quantity=1):
    product = CephDataObject.objects.get(id=ceph_obj_id)
    cart = CartProxy(request) 
    cart.add(product, compute_price(product.data_class), quantity)

def add_to_cart_unique(request, ceph_obj_id):
    product = CephDataObject.objects.get(id=ceph_obj_id)
    cart = CartProxy(request) 
    
    if check_dup_cart_item(cart, ceph_obj_id):
        raise DuplicateCartItemException("Item [{0}] already in cart".format(product.name))
    else:
        cart.add(product, compute_price(product.data_class), 1)
        
def remove_from_cart(request, ceph_obj_id):
    cart = CartProxy(request) 
    cart.remove_item(ceph_obj_id)
    
def remove_all_from_cart(request):
    cart = CartProxy(request) 
    if request.user.is_authenticated():
        cart.delete_old_cart(request.user)

def get_item(cartproxy, ceph_obj_id):
    try:
        #return cartmodels.Item.objects.get(cart=cartproxy.cart, object_id=ceph_obj_id)
        return cart.item_set.filter(object_id=ceph_obj_id)
    except:
        raise ItemDoesNotExist

def check_dup_cart_item(cartproxy, ceph_obj_id):
    try:
        if cartmodels.Item.objects.get(cart=cartproxy.cart, object_id=ceph_obj_id) is not None:
            return True
        else:
            return False
    except:
        return False
