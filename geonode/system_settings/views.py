from django.views.generic.base import TemplateView
from geonode.db_connections import Database
from geonode.system_settings.models import SystemSettings
from geonode.system_settings.system_settings_enum import SystemSettingsEnum
from geonode.layers.models import Layer
import requests


class SystemSettingsView(TemplateView):

    template_name = "system_settings/system_settings.html"
