from django.apps import AppConfig


class WMExtraConfig(AppConfig):
    name = 'wm_extra'
    verbose_name = 'WM Extras'

    def ready(self):
        #import geonode.contrib.worldmap.wm_extra.signals
