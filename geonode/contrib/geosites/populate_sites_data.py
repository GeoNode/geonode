from django.contrib.sites.models import Site


def create_sites():
    Site.objects.all().delete()
    Site.objects.create(name='Master', domain="master.test.org")
    Site.objects.create(name='Slave', domain="slave.test.org")
