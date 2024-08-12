from django.core.management.base import BaseCommand
from cpt.models import Campaign  # Diğer modelleri de buraya ekleyin

class Command(BaseCommand):
    help = 'Flush all data from cpt app'

    def handle(self, *args, **kwargs):
        self.stdout.write('Flushing CPT app data...')
        
        # Tüm verileri sil
        Campaign.objects.all().delete()  # Diğer modelleri de buraya ekleyin

        self.stdout.write(self.style.SUCCESS('Successfully flushed CPT app data.'))

