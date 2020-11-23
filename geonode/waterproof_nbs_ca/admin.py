"""Admin sites for the ``WaterProof NBS CA`` app."""
from django.contrib import admin

from .models import WaterproofNbsCa


class WaterproofNbsCaAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'description', 
             
    )
    

admin.site.register(WaterproofNbsCa, WaterproofNbsCaAdmin)
