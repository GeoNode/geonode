from django.conf.urls import patterns, url

from .views import ProfileRequestList, DataRequestList

urlpatterns = patterns(
    'geonode.datarequests.views',
    
    #url for landing page for profile and data requests
    url(r'^/?$','requests_landing',name='requests_landing'),
    
    #urls for registration
    url(r'^register/verification-sent/$', 'email_verification_send', name='email_verification_send'),
    url(r'^register/email-verified/$', 'email_verification_confirm', name='email_verification_confirm'),
    # url(r'^register/(?P<step>[A-Za-z0-9\-\_]+)/$', signup_wizard, name='signup_step'),
    # url(r'^register/$', signup_wizard, name='signup'),
    url(r'^register/shapefile/$', 'registration_part_two', name='registration_part_two'),
    url(r'^register/$', 'registration_part_one', name='registration_part_one'),

    #urls for profile requests
    url(r'^profile/$', ProfileRequestList.as_view(), name='profile_request_browse'),
    url(r'^profile_requests_csv/$', 'profile_request_csv', name='profile_request_csv'),
    
    url(r'^profile/(?P<pk>\d+)/$', 'profile_request_detail', name="profile_request_detail"),
    url(r'^profile/(?P<pk>\d+)/approve/$', 'profile_request_approve', name="profile_request_approve"),
    url(r'^profile/(?P<pk>\d+)/reject/$', 'profile_request_reject', name="profile_request_reject"),
    url(r'^profile/(?P<pk>\d+)/cancel/$', 'profile_request_cancel', name="profile_request_cancel"),
    url(r'^profile/(?P<pk>\d+)/reconfirm/$', 'profile_request_reconfirm', name="profile_request_reconfirm"), 
    url(r'^prolfile/(?P<pk>\d+)/recreate_dir/$', 'profile_request_recreate_dir', name="profile_request_recreate_dir"), 
    
    url(r'^profile/~count_facets/$', 'profile_request_facet_count', name="profile_request_facet_count"),
    
    #urls for datarequests
    url(r'^data/$', DataRequestList.as_view(), name='data_request_browse'),
    url(r'^data/requests_csv/$', 'data_request_csv', name='data_request_csv'),
    url(r'^data/compute_size/$','data_request_compute_size', name='data_request_compute_size'),
    url(r'^data/reverse_geocode/$','data_request_reverse_geocode', name='data_request_reverse_geocode'),
    
    url(r'^data/(?P<pk>\d+)/$', 'data_request_detail', name="data_request_detail"),
    url(r'^data/(?P<pk>\d+)/approve/$', 'data_request_approve', name="data_request_profile_approve"),
    url(r'^data/(?P<pk>\d+)/reject/$', 'data_request_reject', name="data_request_reject"),
    url(r'^data/(?P<pk>\d+)/cancel/$', 'data_request_cancel', name="data_request_cancel"),
    
    url(r'^data/(?P<pk>\d+)/compute_request_size/$', 'data_request_profile_compute_size', name="data_request_compute_size"), 
    url(r'^data/(?P<pk>\d+)/reverse_geocode/$', 'data_request_profile_reverse_geocode', name="data_request_reverse_geocode"), 
    url(r'^data/assign_grid_refs/$','data_request_assign_gridrefs', name="data_request_assign_gridrefs"),
    
    url(r'^data/~count_facets/$', 'data_request_facet_count', name="data_request_facet_count"),

)
