from django.conf.urls import patterns, url
from geonode.social.views import RecentActivity

urlpatterns = patterns('', url(r'^recent-activity$', RecentActivity.as_view(), name='recent-activity'),)
