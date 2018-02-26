from django.utils.translation import ugettext as _
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document


class ContentTypeEnum(object):
    LAYER = 'layer'
    MAP = 'map'
    DOCUMENT = 'document'

    CONTENT_TYPES = {
        LAYER: Layer,
        MAP: Map,
        DOCUMENT: Document
    }
    
