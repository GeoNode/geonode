from django.conf.urls import patterns, url

from .views import DataRequestPofileList
# from .views import RequesterSignupWizard, DataRequestPofileList

# signup_wizard = RequesterSignupWizard.as_view(url_name='signup_step',
#                                           done_step_name='done')

urlpatterns = patterns(
    'geonode.datarequests.views',

    url(r'^register/verification-sent/$', 'email_verification_send', name='email_verification_send'),
    url(r'^register/email-verified/$', 'email_verification_confirm', name='email_verification_confirm'),
    # url(r'^register/(?P<step>[A-Za-z0-9\-\_]+)/$', signup_wizard, name='signup_step'),
    # url(r'^register/$', signup_wizard, name='signup'),
    url(r'^register/shapefile/$', 'registration_part_two', name='registration_part_two'),
    url(r'^register/$', 'registration_part_one', name='registration_part_one'),

    url(r'^$', DataRequestPofileList.as_view(), name='data_request_browse'),
    url(r'^request_history/$', 'request_history', name='data_request_history'),
    url(r'^(?P<pk>\d+)/$', 'data_request_profile', name="data_request_profile"),
    url(r'^(?P<pk>\d+)/approve/$', 'data_request_profile_approve', name="data_request_profile_approve"),
    url(r'^(?P<pk>\d+)/reject/$', 'data_request_profile_reject', name="data_request_profile_reject"),
    url(r'^(?P<pk>\d+)/reconfirm/$', 'data_request_profile_reconfirm', name="data_request_profile_reconfirm"), 
    url(r'^~count_facets/$', 'data_request_facet_count', name="data_request_facet_count"),

)
