from django.conf.urls.defaults import *


urlpatterns = patterns('geonode.people.views',
    url(r'^forgotname','forgot_username',name='forgot_username'),
)