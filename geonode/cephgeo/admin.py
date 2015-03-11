from django.contrib import admin
from geonode.cephgeo.models import CephDataObject, LayerToCephObjectMap

# Register your models here.
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

    list_filter = ('geo_type', 'grid_ref')
    search_fields = ('name', 'content_type', 'grid_ref',)

class LayerToCephObjectMapAdmin(admin.ModelAdmin):
    model = LayerToCephObjectMap
    list_display_links = ('id',)
    list_display = (
        'id',
        'shapefile',
        'ceph_data_obj',)
    list_filter = ('shapefile', 'ceph_data_obj')
    search_fields = ('shapefile', 'ceph_data_obj')

admin.site.register(CephDataObject, CephDataObjectAdmin)
admin.site.register(LayerToCephObjectMap, LayerToCephObjectMapAdmin)

