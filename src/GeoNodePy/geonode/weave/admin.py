from django.contrib import admin
from geonode.weave.models import Visualization

admin.site.register(Visualization, admin.ModelAdmin)