from django.conf.urls import patterns, url

urlpatterns = patterns('geonode.dvn.views',
                       url(r'^import/?$', 'dvn_import', name='dvn_import'),
                       url(r'^export/?$', 'dvn_export', name="dvn_export")
)