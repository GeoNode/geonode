from django.contrib.gis import admin
from geonode.contrib.dynamic.models import ModelDescription

for md in ModelDescription.objects.all():
    TheModel, TheAdmin = md.get_django_model(with_admin=True)
    admin.site.register(TheModel, TheAdmin)
