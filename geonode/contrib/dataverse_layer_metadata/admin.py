from django.contrib import admin

from geonode.contrib.dataverse_layer_metadata.models import DataverseLayerMetadata
from geonode.contrib.dataverse_layer_metadata.forms import DataverseLayerMetadataAdminForm

class DataverseLayerMetadataAdmin(admin.ModelAdmin):
    form = DataverseLayerMetadataAdminForm
    save_on_top = True
    search_fields = ('map_layer__name',  'dataverse_name', 'dataset_name', 'datafile_label', 'dataset_description')
    list_display = ('map_layer', 'dataset_name', 'datafile_id', 'datafile_label', 'dataverse_name', 'modified',  'created')
    list_filter = ('dataset_is_public', 'dataverse_name', )
    readonly_fields = ('modified', 'created', 'dataset_is_public', 'datafile_create_datetime', 'datafile_expected_md5_checksum' )
    fieldsets = (
           (None, {
               'fields': ('map_layer',)
           }),
         ('Dataverse User', {
                    'fields': (('dv_user_id', 'dv_username', 'dv_user_email'),)
                }),
           ('Dataverse', {
               'fields': ('dataverse_installation_name', ('dataverse_name', 'dataverse_id'), 'dataverse_description')
           }),
            ('Dataset/Dataset Version', {
                  'fields': (('dataset_name', 'dataset_citation')\
                        , 'dataset_is_public'\
                        , ('dataset_semantic_version', 'dataset_id', 'dataset_version_id')\
                        , 'dataset_description')
              }),
              ('Datafile Information', {
                    'fields': (('datafile_label', 'datafile_id')\
                          , ('datafile_filesize', 'datafile_content_type', 'datafile_expected_md5_checksum')\
                          , 'datafile_create_datetime')
                }),
                 ('Dataverse Urls', {
                        'fields': (('return_to_dataverse_url', 'datafile_download_url',),)
                    }),
                ('Timestamps', {
                      'fields': (('created', 'modified'), )
                }),
         )


admin.site.register(DataverseLayerMetadata, DataverseLayerMetadataAdmin)
