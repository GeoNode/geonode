from django.utils.translation import ugettext as _
from geonode.layers.models import Layer


class SystemSettingsEnum(object):
    LOCATION = 'location'
    ELEVATION = 'elevation'
    CONTENT_TYPES = {
        LOCATION: Layer
    }
    SYSTEM_SETTINGS_CHOICES = (
        (LOCATION, _('LOCATION')),
        (ELEVATION, _('ELEVATION')),
    )
