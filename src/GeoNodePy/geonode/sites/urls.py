from django.conf.urls.defaults import patterns, url

js_info_dict = {
    'packages': ('geonode.sites',),
}
urlpatterns = patterns('geonode.sites.views',
    (r'^$', 'site'),

)