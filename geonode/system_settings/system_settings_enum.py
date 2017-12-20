from django.utils.translation import ugettext as _


class SystemSettingsEnum(object):
    LOCATION = 'location'
    ELEVATION = 'elevation'

    SYSTEM_SETTINGS_CHOICES = (
        (LOCATION, _('LOCATION')),
        (ELEVATION, _('ELEVATION')),
    )
