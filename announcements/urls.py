try:
    from django.conf.urls import url, patterns
except ImportError:
    from django.conf.urls.defaults import url, patterns

from announcements.views import detail, dismiss
from announcements.views import CreateAnnouncementView, UpdateAnnouncementView
from announcements.views import DeleteAnnouncementView, AnnouncementListView

urlpatterns = patterns("",
    url(r"^$", AnnouncementListView.as_view(), name="announcements_list"),
    url(r"^announcement/create/$", CreateAnnouncementView.as_view(), name="announcements_create"),
    url(r"^announcement/(?P<pk>\d+)/$", detail, name="announcements_detail"),
    url(r"^announcement/(?P<pk>\d+)/hide/$", dismiss, name="announcements_dismiss"),
    url(r"^announcement/(?P<pk>\d+)/update/$", UpdateAnnouncementView.as_view(), name="announcements_update"),
    url(r"^announcement/(?P<pk>\d+)/delete/$", DeleteAnnouncementView.as_view(), name="announcements_delete"),
)
