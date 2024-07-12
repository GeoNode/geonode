from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    help = 'Deletes all data from the database'

    def handle(self, *args, **kwargs):
        for model in apps.get_models():
            model.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted all data from {model.__name__}'))
