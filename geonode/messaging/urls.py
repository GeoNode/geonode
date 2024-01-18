from django.urls import re_path

from geonode.messaging.views import MarkReadUnread

urlpatterns = [re_path(r"^status/$", MarkReadUnread.as_view(), name="msg_status")]
