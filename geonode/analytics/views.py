from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.db.models import Avg

from geonode.analytics.models.LayerLoad import LayerLoad
from geonode.analytics.models.MapLoad import MapLoad
from geonode.analytics.models.Visitor import Visitor
from geonode.analytics.models.PinpointUserActivity import PinpointUserActivity
import json

# Create your views here.


class AnalyticsView(TemplateView):

    template_name = 'analytics/analytics.html'

    def get_context_data(self, **kwargs):
        context = super(AnalyticsView, self).get_context_data(**kwargs)

        map_loads = MapLoad.objects.all()
        context['map_loads_details'] = map_loads
        context['map_loads'] = map_loads.count()

        pinpoint_activities = PinpointUserActivity.objects.all()
        context['pinpoint_activities'] = pinpoint_activities
        zooms = float(pinpoint_activities.filter(activity_type__contains='zoom').count())
        pans = float(pinpoint_activities.filter(activity_type='pan').count())
        clicks = float(pinpoint_activities.filter(activity_type='click').count())

        if int(map_loads.count()) == 0:
            average_activity_load = 0
        else:
            average_activity_load = int((zooms + pans + clicks) / int(map_loads.count()))

        context['average_activity_load'] = average_activity_load
        context['zooms'] = int(zooms)
        context['pans'] = pans
        context['clicks'] = clicks

        try:
            zooms_data = (zooms / (zooms + pans + clicks))*100
            pans_data = (pans / (zooms + pans + clicks)) * 100
            clicks_data = (clicks / (zooms + pans + clicks)) * 100

        except ZeroDivisionError as e:
            zooms_data = 0
            pans_data = 0
            clicks_data = 0

        chart_data = [{
                'name': 'Zooms',
                'y': zooms_data,
                'sliced': 'true',
                'selected': 'true'
            },
            {
                'name': 'Pans',
                'y': pans_data,

            },
            {
                'name': 'Clicks',
                'y': clicks_data,

            }
        ]

        context['chart_data'] = json.dumps(chart_data)

        try:
            layer_loads = LayerLoad.objects.all()
            context['layer_loads'] = layer_loads
            average_layer_load = layer_loads.aggregate(Avg('layer_id'))
            average_layer_load = round(average_layer_load['layer_id__avg'] / 60, 2)
        except TypeError as e:
            average_layer_load = 0

        context['average_layer_load'] = average_layer_load

        # import pdb;pdb.set_trace()

        return context
