from .models import MapNote
from django.contrib import admin


class MapNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'map', 'title', 'content', 'owner', 'created_dttm', 'modified_dttm')
    date_hierarchy = 'created_dttm'
    search_fields = ['title', 'content']
    ordering = ('-created_dttm',)


admin.site.register(MapNote, MapNoteAdmin)
