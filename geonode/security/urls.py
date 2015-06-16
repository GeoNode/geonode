from django.conf.urls import patterns, url

urlpatterns = patterns('geonode.security.views',
                       url(r'^permissions/(?P<resource_id>\d+)$', 'resource_permissions', name='resource_permissions'),
                       url(r'^bulk-permissions/?$', 'set_bulk_permissions', name='bulk_permissions'),
                       url(r'^request-permissions/?$', 'request_permissions', name='request_permissions'),
                       )
