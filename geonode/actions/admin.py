from django.contrib import admin

from .models import Action


class ActionAdmin(admin.ModelAdmin):
    """
    Admin for Action.
    """
    list_display = ('id', 'timestamp','action_type','description', )
    list_filter  = ('action_type', )
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)


admin.site.register(Action, ActionAdmin)
