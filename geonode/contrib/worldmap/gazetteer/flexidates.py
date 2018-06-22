import exceptions
import logging
from datautil.date import FlexiDate
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.widgets import Input
from django.utils.encoding import smart_str, force_unicode
from django import forms
from django.utils.translation import ugettext as _


logger = logging.getLogger("geonode.flexidates")


class FlexiDateField(models.Field):
    empty_strings_allowed = False

    default_error_messages = {
                                'invalid': _(u"'%s' value has an invalid date format. Acceptable formats include "
                                             u"YYYY-MM-DD where YYYY = year (at least 4 digits, use"
                                             u"0001 for year 1), MM = month (1-12, optional),"
                                             u" DD = day of month (1-31, optional)."
                                             u"For BC dates insert a minus sign before year (-1000-01-01)"
                                             u" or append with BC (1000-01-01 BC).")
    }

    description = _("Date BC/AD (without time)")

    def __init__(self, verbose_name=None, name=None, auto_now=False,
                 auto_now_add=False, **kwargs):
        self.auto_now, self.auto_now_add = auto_now, auto_now_add
        if auto_now or auto_now_add:
            kwargs['editable'] = False
            kwargs['blank'] = True
        models.Field.__init__(self, verbose_name, name, **kwargs)

    def get_internal_type(self):
        return "flexidate"

    def db_type(self, connection):
            return 'varchar'

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, FlexiDate):
            return value

        value = smart_str(value)
        if len(value) == 0:
            return value

        try:
            parsed = parse_flex_date(value)
            if parsed is not None and len(parsed.isoformat()) > 0:
                return parsed
        except ValueError:
            msg = self.error_messages['invalid'] % value
            raise exceptions.ValidationError(msg)

        msg = self.error_messages['invalid_date'] % value
        raise exceptions.ValidationError(msg)

    def get_db_prep_value(self, value, connection, prepared=False):
        # Casts dates into the format expected by the backend
        if not prepared:
            value = self.get_prep_value(value)
        if isinstance(value, FlexiDate):
            connection.ops.value_to_db_date(value.isoformat())
        return connection.ops.value_to_db_date(value)

    def value_to_string(self, obj):
        val = self._get_val_from_obj(obj)
        return '' if val is None else val.isoformat()

    def formfield(self, **kwargs):
        defaults = {'form_class': FlexiDateFormField}

        defaults.update(kwargs)
        return super(FlexiDateField, self).formfield(**defaults)


def parse_flex_date(dateString):
    # from datautil.date import DateutilDateParser
    from dateutil.parser import parse
    # parser = DateutilDateParser()
    # TODO fix this, fails with this error "AttributeError: 'tuple' object has no attribute 'year'"
    if dateString is not None and len(dateString) > 0:
        # return parser.parse(dateString)
        return parse(dateString)
    return None


def parse_julian_date(dateString):
    from jdcal import gcal2jd
    flex_date = parse_flex_date(dateString)
    julian = gcal2jd(int(flex_date.year), int(flex_date.month if flex_date.month is not '' else '1'),
                     int(flex_date.day if flex_date.day is not '' else '1'))
    return julian[0] + julian[1]


class FlexiDateInput(Input):
    input_type = 'text'

    def __init__(self, attrs=None, format=None):
        super(FlexiDateInput, self).__init__(attrs)

    def _format_value(self, value):
        return value

    def _has_changed(self, initial, data):
        # If our field has show_hidden_initial=True, initial will be a string
        # formatted by HiddenInput using formats.localize_input, which is not
        # necessarily the format used for this widget. Attempt to convert it.
        try:
            initial = parse_flex_date(initial).isoformat()
        except (TypeError, ValueError):
            pass
        return super(FlexiDateInput, self)._has_changed(self._format_value(initial), data)


class FlexiDateFormField(forms.Field):
    widget = FlexiDateInput

    default_error_messages = {
        'invalid': _(u"Invalid date format. Try a format of YYYY-MM-DD where YYYY = year (mandatory), "
                     u"MM = month (1-12, optional), DD = day of month (1-31, optional). For BC dates "
                     u"insert a minus sign before year (-1000-01-01) or append with BC (1000-01-01 BC).")
    }

    def __init__(self, *args, **kwargs):
        super(FlexiDateFormField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        # Try to coerce the value to unicode.
        unicode_value = force_unicode(value, strings_only=True)
        if isinstance(unicode_value, unicode):
            value = unicode_value.strip()
        if isinstance(value, unicode):
            if len(value) == 0:
                return None
            try:
                fd = parse_flex_date(value)
                if fd is None:
                    raise ValueError
                return fd
            except ValueError:
                pass
        raise ValidationError(self.error_messages['invalid'])
