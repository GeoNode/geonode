from django.conf.urls import patterns, url

from .views import ProfileRequestList, DataRequestList
# from .views import RequesterSignupWizard, DataRequestPofileList

# signup_wizard = RequesterSignupWizard.as_view(url_name='signup_step',
#                                           done_step_name='done')

urlpatterns = patterns(
    'geonode.datarequests.views',
    url(r'^/?$','requests_landing',name='requests_landing'),
    url(r'^register/verification-sent/$', 'email_verification_send', name='email_verification_send'),
    url(r'^register/email-verified/$', 'email_verification_confirm', name='email_verification_confirm'),
    # url(r'^register/(?P<step>[A-Za-z0-9\-\_]+)/$', signup_wizard, name='signup_step'),
    # url(r'^register/$', signup_wizard, name='signup'),
    url(r'^register/shapefile/$', 'registration_part_two', name='registration_part_two'),
    url(r'^register/$', 'registration_part_one', name='registration_part_one'),

    url(r'^profile/$', ProfileRequestList.as_view(), name='profile_request_browse'),
    url(r'^data/$', DataRequestList.as_view(), name='data_request_browse'),
    url(r'^datarequests_csv/$', 'data_request_csv', name='data_request_csv'),
    url(r'^compute_size/$','data_request_compute_size', name='data_request_compute_size'),
    url(r'^reverse_geocode/$','data_request_reverse_geocode', name='data_request_reverse_geocode'),
    url(r'^profile/(?P<pk>\d+)/$', 'profile_request_detail', name="profile_request_detail"),
    url(r'^data/(?P<pk>\d+)/$', 'data_request_detail', name="data_request_detail"),
    url(r'^(?P<pk>\d+)/approve/$', 'data_request_profile_approve', name="data_request_profile_approve"),
    url(r'^(?P<pk>\d+)/reject/$', 'data_request_profile_reject', name="data_request_profile_reject"),
    url(r'^(?P<pk>\d+)/cancel/$', 'data_request_profile_cancel', name="data_request_profile_cancel"),
    url(r'^(?P<pk>\d+)/reconfirm/$', 'data_request_profile_reconfirm', name="data_request_profile_reconfirm"), 
    url(r'^(?P<pk>\d+)/recreate_dir/$', 'data_request_profile_recreate_dir', name="data_request_profile_recreate_dir"), 
    url(r'^(?P<pk>\d+)/compute_request_size/$', 'data_request_profile_compute_size', name="data_request_profile_compute_size"), 
    url(r'^(?P<pk>\d+)/reverse_geocode/$', 'data_request_profile_reverse_geocode', name="data_request_profile_reverse_geocode"), 
    url(r'^assign_grid_refs/$','data_request_assign_gridrefs', name="data_request_assign_gridrefs"),
    url(r'^~count_facets/$', 'data_request_facet_count', name="data_request_facet_count"),

)
