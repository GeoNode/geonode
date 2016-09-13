from geonode.maps.models import Map, Layer, MapLayer, LayerCategory, LayerAttribute, Contact, ContactRole, Role, MapStats, LayerStats
from django.contrib.contenttypes.models import ContentType
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from dialogos.models import Comment
from django.contrib.contenttypes import generic
from agon_ratings.models import OverallRating, Rating
import autocomplete_light

class MapLayerInline(admin.TabularInline):
    model = MapLayer
    extra = 0

class ContactRoleInline(admin.TabularInline):
    model = ContactRole
    extra = 0
    form = autocomplete_light.modelform_factory(ContactRole)

class MapOverallRatingInline(generic.GenericTabularInline):
    model = OverallRating
    extra = 0

class MapRatingInline(generic.GenericTabularInline):
    model = Rating
    extra = 0
    form = autocomplete_light.modelform_factory(Rating)

class ContactRoleAdmin(admin.ModelAdmin):
    model = ContactRole
    list_display_links = ('id',)
    list_display = ('id','contact', 'layer', 'role')
    list_editable = ('layer', 'role')
    search_fields = ['contact__name','layer__name']
    form = autocomplete_light.modelform_factory(ContactRole)

def remove_map_owners(modeladmin, request, queryset):
    ids = queryset.all().values_list('id', flat=True)
    return HttpResponseRedirect("/users_remove/?ids=%s" % ','.join(str(id) for id in ids))
remove_map_owners.short_description = "Remove the owners of the selected maps"

class MapAdmin(admin.ModelAdmin):
    inlines = [MapLayerInline,MapOverallRatingInline,MapRatingInline]
    list_display = ('id', 'title','owner','created_dttm', 'last_modified')
    list_filter  = ('created_dttm','owner')
    date_hierarchy = 'created_dttm'
    search_fields = ['title','keywords__name']
    actions = [remove_map_owners]
    ordering = ('-created_dttm',)
    form = autocomplete_light.modelform_factory(Map)

class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user')
    search_fields = ['name']
    form = autocomplete_light.modelform_factory(Contact)

class LayerAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'store', 'name', 'date', 'owner', 'topic_category', 'add_as_join_target')
    list_display_links = ('id',)
    list_editable = ('title', 'topic_category')
    list_filter  = ('date', 'date_type', 'constraints_use', 'topic_category', 'owner')
    filter_horizontal = ('contacts',)
    date_hierarchy = 'date'
    readonly_fields = ('uuid', 'typename', 'workspace', 'add_as_join_target')
    inlines = [ContactRoleInline]
    search_fields = ['typename','title']
    actions = ['change_poc']
    ordering = ('-date',)
    form = autocomplete_light.modelform_factory(Layer)

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
    list_display = ('map', 'visits', 'uniques','last_modified')

class LayerStatsAdmin(admin.ModelAdmin):
    list_display = ('layer','visits', 'uniques','downloads','last_modified')




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
#admin.site.register(Comment, CommentAdmin)
