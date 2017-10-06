from django.conf.urls import patterns, url
from django.views.generic import TemplateView


urlpatterns = patterns(
    'geonode.dashboard.views',
    url(r'^_dashboard/?$', TemplateView.as_view(template_name='_dashboard.html'), name='_dashboard'),
    url(r'^_dashboard_grid/?$', TemplateView.as_view(template_name='_dashboard_grid.html'), name='_dashboard_grid'),
    url(r'^favourite_list/?$', TemplateView.as_view(template_name='favourite_list.html'), name='favourite_list'),
    url(r'^_featured_list/?$', TemplateView.as_view(template_name='_featured_list.html'), name='_featured_list'),


    #database backup and restore
    url(r'^database-backup/metadata$', 'metadatabackup', name='metadata-backup'),
    url(r'^database-backup/data$', 'databackup', name='data-backup'),


    url(r'^uploaded-folder-backup$', 'uploadedFolderBackup', name='uploaded-folder-backup'),
    url(r'^data-folder-backup$', 'geoserverDataFolderBackup', name='data-folder-backup'),


)
