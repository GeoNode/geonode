from django.conf.urls.defaults import *


urlpatterns = patterns('geonode.registration.views',
    (r'^forgotname','forgotUsername'),
    (r'', include('registration.urls')),
)