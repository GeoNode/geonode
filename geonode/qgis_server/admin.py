__author__ = 'ismailsunni'
__project_name__ = 'geonode'
__filename__ = 'admin'
__date__ = '1/28/16'
__copyright__ = 'imajimatika@gmail.com'


from django.contrib import admin
from geonode.qgis_server.models import QGISServerLayer


# Register your models here.
class QGISServerLayerAdmin(admin.ModelAdmin):
    list_display = [
        'layer',
        'base_layer_path'
    ]

admin.site.register(QGISServerLayer, QGISServerLayerAdmin)
