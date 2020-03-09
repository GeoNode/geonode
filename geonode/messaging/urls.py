from django.conf.urls import url

from geonode.messaging.views import MarkReadUnread

urlpatterns = [
    url(r'^status/$', MarkReadUnread.as_view(), name='msg_status')
]
