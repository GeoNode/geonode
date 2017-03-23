from django.contrib import admin

from .models import Database


class DatabaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'strategy_type', 'layers_count', 'created_at', )


admin.site.register(Database, DatabaseAdmin)
