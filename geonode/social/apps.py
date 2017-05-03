from django.apps import apps, AppConfig
from actstream import registry


class SocialConfig(AppConfig):
    name = 'geonode.social'

    def ready(self):
        registry.register(apps.get_app_config('layers').get_model('Layer'))
        registry.register(apps.get_app_config('maps').get_model('Map'))
        registry.register(apps.get_app_config('documents').get_model('Document'))
        registry.register(apps.get_app_config('people').get_model('Profile'))
        registry.register(apps.get_app_config('services').get_model('Service'))
        registry.register(apps.get_app_config('dialogos').get_model('Comment'))
