from django.contrib import admin

from .models import Intake

class IntakeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description',
    )

admin.site.register(Intake, IntakeAdmin)