from django.conf.urls import patterns, url

urlpatterns = patterns(
    'geonode.arealocate.views',
    
    url(r'^$', 'geocode', name='geocode'),
)

