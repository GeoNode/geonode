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
        'data_class',
        'grid_ref',
        'size_in_bytes',)
    list_filter = ('data_class','content_type', 'grid_ref')
    search_fields = ('name', 'data_class', 'content_type', 'grid_ref',)

class FTPRequestAdmin(admin.ModelAdmin):
    model = FTPRequest
    list_display_links = ('id','name')
    list_display = (
        'id',
        'name',
        'date_time',
        'user',
        'status',
        'num_tiles',
        'size_in_bytes',)
    list_filter = ('user', 'status',)
    search_fields = ('name', 'user__username', 'status',)

class FTPRequestToObjectIndexAdmin(admin.ModelAdmin):
    model = FTPRequestToObjectIndex
    list_display_links = ('id',)
    list_display = (
        'id',
        'ftprequest',
        'cephobject',)
    list_filter = ('cephobject', 'ftprequest',)
    search_fields = ('cephobject__name', 'ftprequest__name',)

class UserJurisdictionAdmin(admin.ModelAdmin):
    model = UserJurisdiction
    list_display_links = ('id',)
    list_display = (
        'id',
        'user',
#        'group',
        'jurisdiction_shapefile',)
#    list_filter = ('group',)
    search_fields = ('user__username', 
#                     'group', 
                     'jurisdiction_shapefile__title',)

class MissionGridRefAdmin(admin.ModelAdmin):
    model = MissionGridRef
    list_display = ('id',)
    list_display = (
        'id',
        'grid_ref',
        'fieldID'
        )
    list_filter = ('grid_ref','fieldID')
    search_fields = ('grid_ref','fieldID')

admin.site.register(Cart, CartAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(CephDataObject, CephDataObjectAdmin)
admin.site.register(FTPRequest, FTPRequestAdmin)
admin.site.register(FTPRequestToObjectIndex, FTPRequestToObjectIndexAdmin)
admin.site.register(UserJurisdiction, UserJurisdictionAdmin)
admin.site.register(MissionGridRef,MissionGridRefAdmin)

