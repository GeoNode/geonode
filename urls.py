from django.conf.urls.defaults import patterns, url

js_info_dict = {
    'packages': ('geonode.analytics',),
}

urlpatterns = patterns('geonode.analytics.views',
    url(r'^$', 'analytic_list', name='analytics_browse'))
