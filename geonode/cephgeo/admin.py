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
    search_fields = ('user__username', 'creation_date')


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


class FTPRequestAdmin(admin.ModelAdmin):
    model = FTPRequest
    list_display_links = ('id', 'name')
    list_display = (
        'id',
        'name',
        'date_time',
        'user',
        'status',
        'num_tiles',
        'size_in_bytes',)
    list_filter = ('status',)
    search_fields = ('name', 'user__username', 'status',)


class FTPRequestToObjectIndexAdmin(admin.ModelAdmin):
    model = FTPRequestToObjectIndex
    list_display_links = ('id',)
    list_display = (
        'id',
        'ftprequest',
        'cephobject',)
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
    list_display_links = ('id',)
    list_display = (
        'id',
        'grid_ref',
        'fieldID'
    )
    list_filter = ('fieldID',)
    search_fields = ('grid_ref', 'fieldID')


class SucToLayerAdmin(admin.ModelAdmin):
    model = SucToLayer
    list_display_links = ('id',)
    list_display = (
        'id',
        'suc',
        'block_name'
    )
    list_filter = ('suc',)
    search_fields = ('suc', 'block_name')


class RIDFAdmin(admin.ModelAdmin):
    model = RIDF
    list_display_links = ('id',)
    list_display = (
        'id',
        'prov_code',
        'prov_name',
        'muni_code',
        'muni_name',
        'iscity',
        '_5yr',
        '_25yr',
        '_100yr',
        'rbs_raw',
        'Riverbasins',

    )
    # list_filter = ('')

    def get_queryset(self, request):
        return super(RIDFAdmin, self).get_queryset(request).prefetch_related('riverbasins')

    def Riverbasins(self, obj):
        return u", ".join(o.name for o in obj.riverbasins.all())

    search_fields = ('muni_code', 'muni_name', 'iscity', 'prov_code', 'prov_name', '_100yr',
                     '_25yr', '_5yr', 'rbs_raw')


class UserTilesAdmin(admin.ModelAdmin):
    model = UserTiles
    list_display_links = ('id',)
    list_display = (
        'id',
        'user',
        'num_tiles'
    )
    search_fields = ('user__username', 'gridref_list')


class TileDataClassAdmin(admin.ModelAdmin):
    model = TileDataClass
    list_display_links = ('short_name',)
    list_display = (
        'id',
        'short_name',
        'full_name',
        'description',
    )


class LidarCoverageBlockAdmin(admin.ModelAdmin):
    model = LidarCoverageBlock
    list_display_links = ('uid', 'block_name',)
    list_display = (
        'uid',
        'block_name',
        'adjusted_l',
        'sensor',
        'processor',
        'flight_num',
        'mission_na',
        'date_flown',
        # 'x_shift_m',
        # 'y_shift_m',
        # 'z_shift_m',
        # 'height_dif',
        # 'rmse_val_m',
        # 'cal_ref_pt',
        # 'val_ref_pt',
        'floodplain',
        'pl1_suc',
        'pl2_suc',
    )
    list_filter = ('sensor', 'pl1_suc', 'pl2_suc')
    search_fields = ('uid', 'block_name', 'sensor', 'processor',
                     'flight_num', 'mission_na', 'date_flown', 'floodplain', 'pl1_suc', 'pl2_suc')


class CephDataObjectAdmin(admin.ModelAdmin):
    model = CephDataObject
    list_display_links = ('id',)
    list_display = (
        'id',
        'name',
        'block_uid',
        # 'block__block_name',
        'file_hash',
        'last_modified',
        'content_type',
        'data_class',
        'grid_ref',
        'size_in_bytes',)
    list_filter = ('data_class', 'content_type')
    search_fields = ('name', 'data_class', 'content_type',
                     'grid_ref', 'block_uid__uid', 'block_uid__block_name')


admin.site.register(Cart, CartAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(CephDataObject, CephDataObjectAdmin)
admin.site.register(FTPRequest, FTPRequestAdmin)
admin.site.register(FTPRequestToObjectIndex, FTPRequestToObjectIndexAdmin)
admin.site.register(UserJurisdiction, UserJurisdictionAdmin)
admin.site.register(MissionGridRef, MissionGridRefAdmin)
admin.site.register(SucToLayer, SucToLayerAdmin)
admin.site.register(RIDF, RIDFAdmin)
admin.site.register(UserTiles, UserTilesAdmin)
admin.site.register(TileDataClass, TileDataClassAdmin)
admin.site.register(LidarCoverageBlock, LidarCoverageBlockAdmin)
