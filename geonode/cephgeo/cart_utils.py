from changuito import CartProxy
from changuito import models as cartmodels
from changuito.proxy import ItemDoesNotExist
from geonode.cephgeo.models import CephDataObject
from django.contrib import messages
import utils

class DuplicateCartItemException(Exception):
    pass

PRICING = {
	"LAZ file"      : 1.00,
	"DEM TIF"       : 2.00,
	"DSM TIF"       : 2.00,
	"Orthophoto"    : 3.00,
}

def compute_price(geo_type):
    try:
        return PRICING[geo_type]
    except KeyError as e:
        raise KeyError("No valid pricing for geo-type [{0}]".format(geo_type))

def add_to_cart(request, ceph_obj_id, quantity=1):
    product = CephDataObject.objects.get(id=ceph_obj_id)
    cart = CartProxy(request) 
    cart.add(product, compute_price(product.geo_type), quantity)

def add_to_cart_unique(request, ceph_obj_id):
    product = CephDataObject.objects.get(id=ceph_obj_id)
    cart = CartProxy(request) 
    
    if check_dup_cart_item(cart, ceph_obj_id):
        raise DuplicateCartItemException("Item [{0}] already in cart".format(product.name))
    else:
        cart.add(product, compute_price(product.geo_type), 1)
        
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
