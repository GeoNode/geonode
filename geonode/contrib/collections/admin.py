from django.contrib import admin

from .models import Collection


class CollectionAdmin(admin.modelAdmin):
     prepopulated_fields = {"slug": ("name",)}


admin.site.register(Collection, CollectionAdmin)
