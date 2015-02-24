from django.contrib import admin
from geonode.cephgeo.models import CephDataObject, LayerToCephObjectMap

class CephDataObjectAdmin(admin.ModelAdmin):
    model = CephDataObject
    list_display_links = ('id',)
    list_display = (
        'id',
        'name',
        'file_ext',
        'grid_ref',)
    list_filter = ('file_ext', 'grid_ref')
    search_fields = ('name', 'file_ext', 'grid_ref',)

class LayerToCephObjectMapAdmin(admin.ModelAdmin):
    model = LayerToCephObjectMap
    list_display_links = ('id',)
    list_display = (
        'id',
        'shapefile',
        'ceph_data_obj',)
    list_filter = ('shapefile', 'ceph_data_obj')
    search_fields = ('shapefile', 'ceph_data_obj')
