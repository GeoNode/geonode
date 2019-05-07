from django.apps import AppConfig


class WMExtraConfig(AppConfig):
    name = 'geonode.contrib.worldmap.wm_extra'
    verbose_name = 'WM Extras'

    def ready(self):
        from geonode.contrib.worldmap.wm_extra import signals  # noqa
