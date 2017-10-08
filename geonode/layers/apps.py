from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = 'geonode.layers'

    def ready(self):
        from actstream import registry
        registry.register(self.get_model('Layer'))