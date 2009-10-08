from django.conf.urls.defaults import *
from piston.authentication import HttpBasicAuthentication
from piston.doc import documentation_view

from geonode.layers.handlers import LayerHandler

auth = HttpBasicAuthentication(realm='My sample API')

layers = Resource(handler=LayerHandler, authentication=auth) 

urlpatterns = patterns('',
    url(r'^layers/$', layers),
    url(r'^layers/(?P<emitter_format>.+)/$', layers),
    url(r'^layers\.(?P<emitter_format>.+)', layers, name='layers'),

    # automated documentation
    url(r'^docs$', documentation_view),
)
