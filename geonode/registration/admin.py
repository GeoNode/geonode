from django.contrib import admin
from geonode.registration.models import Province, Municipality

# Register your models here.
class ProvinceAdmin(admin.ModelAdmin):
    model = Province
    list_display_links = ("province_name")
    list_display = (
        "id",
        "province_name"
    )
    
class MunicipalityAdmin(admin.ModelAdmin):
    model = Municipality
    list_display_links = ("id")
    list_display = (
        "id",
        "municipality_name",
        "province"
    )
    list_filter = ("province","municipality_name")
    search_fields = ("province","municipality_name","alt_name")
    
admin.site.register(Province,ProvinceAdmin)
admin.site.register(Municipality, MunicipalityAdmin)
    
