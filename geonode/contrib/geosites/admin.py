from django.contrib import admin

from .models import SiteResources, SitePeople


class SiteResourceAdmin(admin.ModelAdmin):
    filter_horizontal = ('resources',)
    readonly_fields = ('site',)


class SitePeopleAdmin(admin.ModelAdmin):
    filter_horizontal = ('people',)
    readonly_fields = ('site',)


admin.site.register(SiteResources, SiteResourceAdmin)
admin.site.register(SitePeople, SitePeopleAdmin)
