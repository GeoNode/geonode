from django.conf.urls import patterns, url

urlpatterns = patterns(
    'geonode.datarequests.views',
    
    url(r'^$', 'geocode', name='geocode'),
)
