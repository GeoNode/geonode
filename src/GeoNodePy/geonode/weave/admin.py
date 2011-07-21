from django.contrib import admin
from geonode.weave.models import Visualization

from jsonfield.fields import JSONField
from geonode.weave.widgets import JSONWidget

class VisualizationAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {'widget': JSONWidget},
    }

admin.site.register(Visualization, VisualizationAdmin)