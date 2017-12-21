from django.views.generic.base import TemplateView
from geonode.db_connections import Database
from geonode.system_settings.models import SystemSettings
from geonode.system_settings.system_settings_enum import SystemSettingsEnum
from geonode.layers.models import Layer
import requests


class SystemSettingsView(TemplateView):

    template_name = "system_settings/system_settings.html"

    def get_context_data(self, **kwargs):
        context = super(SystemSettingsView, self).get_context_data(**kwargs)

        location_settings = SystemSettings.objects.get(settings_code=SystemSettingsEnum.LOCATION)

        layer = Layer.objects.get(id=location_settings.object_id)
        db = Database(db_name=layer.store)
        table_schema = db.get_table_schema_info(table_name=str(layer.name))

        columns_name = list()
        for column in table_schema:
            columns_name.append(str(column.column_name).lower())

        if 'post_code' or 'road_no' or 'house_no' not in columns_name:
            context['layer_message'] = "This layer does not have necessary data for location search!"

        # import pdb;pdb.set_trace()

        return context

