from geonode.maps.models import Map, Layer, MapLayer, LayerCategory, LayerAttribute, Contact, ContactRole, Role, MapStats, LayerStats
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
    search_fields = ['contact','layer']

class MapAdmin(admin.ModelAdmin):
    inlines = [MapLayerInline,]
    list_display = ('id', 'title','owner','created_dttm', 'last_modified')
    list_filter  = ('created_dttm','owner')
    date_hierarchy = 'created_dttm'
    search_fields = ['title','keywords']
    

class ContactAdmin(admin.ModelAdmin):
    inlines = [ContactRoleInline]
    list_display = ('id', 'name', 'user')
    search_fields = ['name']

class LayerAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'date', 'owner', 'topic_category')
    list_display_links = ('id',)
    list_editable = ('title', 'topic_category')
    list_filter  = ('date', 'date_type', 'constraints_use', 'topic_category', 'owner')
    filter_horizontal = ('contacts',)
    date_hierarchy = 'date'
    readonly_fields = ('uuid', 'typename', 'workspace') 
    inlines = [ContactRoleInline]
    search_fields = ['typename','title']
    actions = ['change_poc']

    def change_poc(modeladmin, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(reverse('change_poc', kwargs={"ids": "_".join(selected)}))
    change_poc.short_description = "Change the point of contact for the selected layers"

class LayerCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'title')
    list_display_links = ('name', 'title')


class LayerAttributeAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'attribute_label', 'layer', 'attribute_type', 'searchable')
    list_filter  = ('layer', 'searchable', 'attribute_type')

class MapLayerAdmin(admin.ModelAdmin):
    list_display = ('id','map', 'name', 'ows_url', 'stack_order')
    list_display_links = ('id',)
    list_editable = ('name', 'stack_order')
    list_filter  = ('ows_url',)
    search_fields = ['map__title', 'map__owner__username', 'name','layer_params','ows_url']

class MapStatsAdmin(admin.ModelAdmin):
    list_display = ('map', 'visits', 'uniques')

class LayerStatsAdmin(admin.ModelAdmin):
    list_display = ('layer','visits', 'uniques','downloads')

admin.site.register(Map, MapAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Layer, LayerAdmin)
admin.site.register(LayerCategory, LayerCategoryAdmin)
admin.site.register(LayerAttribute, LayerAttributeAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(MapLayer,MapLayerAdmin)
admin.site.register(Role)
admin.site.register(MapStats, MapStatsAdmin)
admin.site.register(LayerStats, LayerStatsAdmin)
