from django.contrib import admin

from geonode.dataverse_layer_metadata.models import DataverseLayerMetadata
from geonode.dataverse_layer_metadata.forms import DataverseLayerMetadataAdminForm

class DataverseLayerMetadataAdmin(admin.ModelAdmin):
    form = DataverseLayerMetadataAdminForm
    save_on_top = True
    search_fields = ('map_layer__name',  'dataverse_name', 'dataset_name', 'datafile_label', 'dataset_description')
    list_display = ('map_layer', 'dataset_name', 'datafile_label', 'dataverse_name', )
    list_filter = ('dataverse_name', )   
    readonly_fields = ('modified', 'created', 'datafile_create_datetime', 'datafile_expected_md5_checksum' )
    fieldsets = (
           (None, {
               'fields': ('map_layer',)
           }),
           ('Dataverse', { 
               'fields': ('dataverse_installation_name', ('dataverse_name', 'dataverse_id'), 'dataverse_description')
           }),
            ('Dataset/Dataset Version', { 
                  'fields': (('dataset_name', 'dataset_citation')\
                        , ('dataset_semantic_version', 'dataset_id', 'dataset_version_id')\
                        , 'dataset_description')
              }),
              ('Datfile Info', { 
                    'fields': (('datafile_label', 'datafile_id')\
                          , ('datafile_filesize', 'datafile_content_type', 'datafile_expected_md5_checksum')\
                          , 'datafile_create_datetime')
                }),      
                ('Timestamps', { 
                      'fields': (('created', 'modified'), )
                }),      
         )
                
               
admin.site.register(DataverseLayerMetadata, DataverseLayerMetadataAdmin)

