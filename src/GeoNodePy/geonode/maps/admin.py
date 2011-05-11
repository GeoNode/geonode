from geonode.maps.models import Map, Layer, MapLayer, Contact, ContactRole, Role
from django.contrib.contenttypes.models import ContentType
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse


class MapLayerInline(admin.TabularInline):
    model = MapLayer

class ContactRoleInline(admin.TabularInline):
    model = ContactRole

class ContactRoleAdmin(admin.ModelAdmin):
    model = ContactRole
    list_display_links = ('id',)
    list_display = ('id','contact', 'layer', 'role')
    list_editable = ('contact', 'layer', 'role')

class MapAdmin(admin.ModelAdmin):
    inlines = [MapLayerInline,]

class ContactAdmin(admin.ModelAdmin):
    inlines = [ContactRoleInline]

class LayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'typename','service_type','title', 'date', 'topic_category')
    list_display_links = ('id',)
    list_editable = ('title', 'topic_category')
    list_filter  = ('date', 'date_type', 'constraints_use', 'topic_category')
    filter_horizontal = ('contacts',)
    date_hierarchy = 'date'
    readonly_fields = ('uuid', 'typename', 'workspace') 
    inlines = [ContactRoleInline]

    actions = ['change_poc']

    def change_poc(modeladmin, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(reverse('change_poc', kwargs={"ids": "_".join(selected)}))
    change_poc.short_description = "Change the point of contact for the selected layers"

admin.site.register(Map, MapAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Layer, LayerAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(MapLayer)
admin.site.register(Role)
