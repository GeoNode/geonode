from django.contrib import admin
from geonode.cephgeo.models import *
from changuito.models import Cart, Item

# Register your models here.
class CartAdmin(admin.ModelAdmin):
    model = Cart
    list_display_links = ('id',)
    list_display = (
        'id',
        'user',
        'creation_date',
        'checked_out',
        'item_set')

class ItemAdmin(admin.ModelAdmin):
    model = Item
    list_display_links = ('id',)
    list_display = (
        'id',
        'cart',
        'quantity',
        'unit_price',
        'content_type',
        'object_id',)

class CephDataObjectAdmin(admin.ModelAdmin):
    model = CephDataObject
    list_display_links = ('id',)
    list_display = (
        'id',
        'name',
        'file_hash',
        'last_modified',
        'content_type',
        'geo_type',
        'grid_ref',
        'size_in_bytes',)
    list_filter = ('content_type', 'grid_ref')
    search_fields = ('name', 'content_type', 'grid_ref',)

admin.site.register(Cart, CartAdmin)
admin.site.register(CephDataObject, CephDataObjectAdmin)

