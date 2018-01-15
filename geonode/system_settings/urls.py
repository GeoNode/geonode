from django.conf.urls import url, include

from api.views import SystemSettingsSaveAPIView, SystemSettingsAPIView, MissingAttributeAPIView
from .views import SystemSettingsView

urlpatterns = [

    url(r'^api/address/attributes/(?P<uuid>[\w-]+)/$', MissingAttributeAPIView.as_view()),
    url(r'^api/settings/save/$', SystemSettingsSaveAPIView.as_view()),

    url(r'^api/system/settings/$', SystemSettingsAPIView.as_view()),

    url(r'^', SystemSettingsView.as_view(), name='system_settings'),

]
