from piston.handler import BaseHandler, AnonymousBaseHandler
from GeoNode.maps.models import Map

class MapHandler(BaseHandler):
    """
    Authenticate entry point for adding and update maps
    """
    model = Map
    anonymous = 'AnonymousMapHandler'
    fields = ('title', 'abstract', 'contact', 'featured',
              'zoom', 'center_lat', 'center_lon',
              ('author', ('username',))

    @classmethod
    def content_length(cls, map_):
        return len(map_.content)

    @classmethod
    def resource_uri(cls, map_):
        return ('maps', [ 'json', ])

    def read(self, request, mapid):
        """
        """
        base = Map.objects
        
        if mapid:
            return base.get(pk=mapid)
        else:
            return base.all()
