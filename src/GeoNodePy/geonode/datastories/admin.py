from django.contrib import admin
from geonode.datastories.models import Datastory, Page, Visualizationpage, Mappage

admin.site.register(Datastory, admin.ModelAdmin)
admin.site.register(Page, admin.ModelAdmin)
admin.site.register(Visualizationpage, admin.ModelAdmin)
admin.site.register(Mappage, admin.ModelAdmin)