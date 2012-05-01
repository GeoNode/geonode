__author__ = 'mbertrand'


from django.utils import simplejson
from piston.emitters import Emitter
from geojson import

class GazetteerGeoJSONEmitter(Emitter):
    """
    JSON emitter, understands timestamps, wraps result set in object literal
    for Ext JS compatibility
    """
    def render(self, request):
        data = self.construct()
        geojson_items = []
        for item in data:
            geojson_items.append((geojson.(
                title = item['title'],
                description = item['synopsis'],
                link = item['url'],
                pubDate = item['date_created'],
            )))

Emitter.register('ext-json', ExtJSONEmitter, 'application/json; charset=utf-8')