from geonode.annotations.models import Annotation
from django.contrib import admin

class AnnotationAdmin(admin.ModelAdmin):
    list_display = ('id', 'map', 'title')
    list_filter = ('map','in_map', 'in_timeline',)
    search_fields = ('map__title', 'title', 'content',)


admin.site.register(Annotation, AnnotationAdmin)