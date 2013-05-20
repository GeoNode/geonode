from geonode.mapnotes.models import MapNote
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from dialogos.models import Comment
import autocomplete_light
from django.contrib.contenttypes import generic

class MapNoteCommentInline(generic.GenericTabularInline):
    model = Comment
    extra = 0
    form = autocomplete_light.modelform_factory(Comment)

    
class MapNoteAdmin(admin.ModelAdmin):
    inlines = [MapNoteCommentInline,]
    list_display = ('id', 'map', 'title','content', 'owner','created_dttm', 'modified_dttm')
    date_hierarchy = 'created_dttm'
    search_fields = ['title','content']
    ordering = ('-created_dttm',)
    form = autocomplete_light.modelform_factory(MapNote)
    
admin.site.register(MapNote, MapNoteAdmin)