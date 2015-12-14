from django.conf.urls.defaults import *
from geonode.register.views import registerOrganizationUser, registercompleteOrganizationUser, forgotUsername
from geonode.register.forms import UserRegistrationForm

urlpatterns = patterns('',
                       url(r'^register/$',
                           registerOrganizationUser,
                           {'form_class' : UserRegistrationForm},
                           name='registration_register'),
                       url(r'^registercomplete/$',
                           registercompleteOrganizationUser,
                           name='registration_complete'),
                       url(r'^forgotname/$',
                           forgotUsername, name='forgotname'),
                       (r'', include('registration.urls')),
                       )
