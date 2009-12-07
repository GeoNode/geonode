from capra.hazard.models import Hazard, Period, Layer
from django.contrib import admin

class PeriodInline(admin.TabularInline):
    model = Period

class HazardAdmin(admin.ModelAdmin):
    inlines = [PeriodInline,]

admin.site.register(Hazard, HazardAdmin)
admin.site.register(Period)
