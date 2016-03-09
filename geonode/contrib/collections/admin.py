from django.contrib import admin

from .models import Collection


class CollectionAdmin(admin.ModelAdmin):
     prepopulated_fields = {"slug": ("name",)}


admin.site.register(Collection, CollectionAdmin)
