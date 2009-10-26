from django.conf.urls.defaults import *
from django.conf import settings
from geonode.urls import urlpatterns

urlpatterns += patterns('capra.hazard.views',
    (r'^hazard/report(.(?P<format>html|pdf))?', 'report'),
    (r'^hazard/', 'index'),
)


if settings.DEBUG:
    import os
    def here(*x): 
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

    root = here("..", "..", "capra-client", "build", "capra-client") if settings.MINIFIED_RESOURCES else here("..", "..", "capra-client", "")
    urlpatterns += patterns('',
        (r'^capra_static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': root}),
    )
