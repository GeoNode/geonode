from geonode.layers.models import Layer
from django.contrib import admin

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

    def change_poc(self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(reverse('change_poc', kwargs={"ids": "_".join(selected)}))
    change_poc.short_description = "Change the point of contact for the selected layers"

admin.site.register(Layer, LayerAdmin)

