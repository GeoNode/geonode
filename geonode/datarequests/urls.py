from django.conf.urls import patterns, url

from .views import ProfileRequestList, DataRequestList, DataRequestProfileList

urlpatterns = patterns(
    'geonode.datarequests.views',

    #url for landing page for profile and data requests
    url(r'^/?$','requests_landing',name='requests_landing'),
    url(r'^requests_csv/$','requests_csv',name='requests_csv'),
    url(r'^old_requests/$',DataRequestProfileList.as_view(),name='old_request_model_view'),

    #old requests
    url(r'^old_requests/$',DataRequestProfileList.as_view(),name='old_requests_model_view'),
    url(r'^old_requests/csv$','old_requests_csv',name='old_requests_csv'),
    url(r'^old_requests/(?P<pk>\d+)/$', 'old_request_detail', name="old_request_detail"),
    url(r'^old_requests/migrate/$','old_request_migration_all',name='old_request_migration_all'),
    url(r'^old_requests/(?P<pk>\d+)/migrate/$','old_request_migration', name='old_request_migration'),
    url(r'^old_requests/~count_facets/$','old_request_facet_count', name='old_request_facet_count'),

    #urls for registration
    url(r'^register/$','register',name='request_register'),
    # Start of part 2 registration
    url(r'^register/data_request/$', 'data_request_view', name='data_request_form'),
    # Resolve /register/profile_request, proceed to ./views/registration.py/ profile_request_view
    url(r'^register/profile_request/$', 'profile_request_view', name='profile_request_form'),
    # Insert a landing page: registration success 
    url(r'^register/register_success/$', 'register_success', name='register_success'),
    url(r'^register/verification-sent/$', 'email_verification_send', name='email_verification_send'),
    url(r'^register/email-verified/$', 'email_verification_confirm', name='email_verification_confirm'),

    #urls for profile requests
    url(r'^profile/$', ProfileRequestList.as_view(), name='profile_request_browse'),
    url(r'^profile_requests_csv/$', 'profile_requests_csv', name='profile_requests_csv'),

    # See here pending users?
    url(r'^profile/(?P<pk>\d+)/$', 'profile_request_detail', name="profile_request_detail"),
    url(r'^profile/(?P<pk>\d+)/edit/$', 'profile_request_edit', name="profile_request_edit"),
    url(r'^profile/(?P<pk>\d+)/approve/$', 'profile_request_approve', name="profile_request_approve"),
    url(r'^profile/(?P<pk>\d+)/reject/$', 'profile_request_reject', name="profile_request_reject"),
    url(r'^prolfile/(?P<pk>\d+)/cancel/$', 'profile_request_cancel', name="profile_request_cancel"),
    url(r'^profile/(?P<pk>\d+)/reconfirm/$', 'profile_request_reconfirm', name="profile_request_reconfirm"),
    url(r'^prolfile/(?P<pk>\d+)/recreate_dir/$', 'profile_request_recreate_dir', name="profile_request_recreate_dir"),
    url(r'^profile/~count_facets/$', 'profile_request_facet_count', name="profile_request_facet_count"),

    #urls for datarequests
    url(r'^data/$', DataRequestList.as_view(), name='data_request_browse'),
    url(r'^data/data_requests_csv/$', 'data_requests_csv', name='data_requests_csv'),
    url(r'^data/compute_size/$','data_request_compute_size_all', name='data_request_compute_size_all'),
    url(r'^data/reverse_geocode/$','data_request_reverse_geocode_all', name='data_request_reverse_geocode_all'),
    url(r'^data/tag_suc/$', 'data_request_tag_suc_all', name="data_request_tag_suc_all"),

    url(r'^data/(?P<pk>\d+)/$', 'data_request_detail', name="data_request_detail"),
    url(r'^data/(?P<pk>\d+)/edit/$', 'data_request_edit', name="data_request_edit"),
    url(r'^data/(?P<pk>\d+)/approve/$', 'data_request_approve', name="data_request_approve"),
    url(r'^data/(?P<pk>\d+)/reject/$', 'data_request_reject', name="data_request_reject"),
    url(r'^data/(?P<pk>\d+)/cancel/$', 'data_request_cancel', name="data_request_cancel"),

    url(r'^data/(?P<pk>\d+)/compute_request_size/$', 'data_request_compute_size', name="data_request_compute_size"),
    url(r'^data/(?P<pk>\d+)/tag_suc/$', 'data_request_tag_suc', name="data_request_tag_suc"),
    url(r'^data/(?P<pk>\d+)/notify_suc/$', 'data_request_notify_suc', name="data_request_notify_suc"),
    url(r'^data/(?P<pk>\d+)/notify_requester/$', 'data_request_notify_requester', name="data_request_notify_requester"),
    url(r'^data/(?P<pk>\d+)/forward_request/$', 'data_request_forward_request', name="data_request_forward_request"),
    url(r'^data/(?P<pk>\d+)/reverse_geocode/$', 'data_request_reverse_geocode', name="data_request_reverse_geocode"),
    url(r'^data/assign_grid_refs/$','data_request_assign_gridrefs', name="data_request_assign_gridrefs"),
    url(r'^data/(?P<pk>\d+)/assign_grid_refs/$', 'data_request_assign_gridrefs_user', name="data_request_assign_gridrefs_user"), 

    url(r'^data/~count_facets/$', 'data_request_facet_count', name="data_request_facet_count"),

)
