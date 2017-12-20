from django.conf.urls import url, include

# from .views import LocationView, LayersAttributesAPIView
from api.views import LayersAttributesAPIView, SystemSettingsSaveAPIView, SystemSettingsAPIView
from .views import SystemSettingsView

urlpatterns = [

    # url(r'^api/layers/attributes/', LayersAttributesAPIView.as_view()),
    url(r'^api/settings/save/', SystemSettingsSaveAPIView.as_view()),

    url(r'^api/system/settings/', SystemSettingsAPIView.as_view()),

    url(r'^', SystemSettingsView.as_view(), name='system_settings'),

]
