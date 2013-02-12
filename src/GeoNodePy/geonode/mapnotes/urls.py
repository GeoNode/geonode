from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('geonode.mapnotes.views',
    url(r'^(?P<mapid>[0-9]*)$', 'annotations', name='annotations'),
    url(r'^(?P<mapid>[0-9]*)/(?P<id>[0-9]*)$', 'annotations', name='annotations'),
    url(r'^(?P<id>[0-9]*)/details$', 'annotation_details', name='annotation_details'),
)    