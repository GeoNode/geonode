from django.conf.urls.defaults import *

urls = patterns('capra.hazard',
    r'^$', 'views.index'
