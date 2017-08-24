from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _

"""
Specify Data Table Delimiter Choices
"""
#   Delimiter choices
#   For each delimiter, specify a "varname", "value", and "friendly_name"
#
DELIMITER_TYPE_INFO = ( dict(varname='COMMA', value=',', friendly_name='Comma Separated (.csv)'),
                        dict(varname='TAB', value='\t', friendly_name='Tab Separated (.tab)'),
                    )
assert len(DELIMITER_TYPE_INFO) > 1, "DELIMITER_TYPE_INFO must have at least one value"

DELIMITER_TYPE_CHOICES = [ (dt['varname'], dt['friendly_name']) for dt in DELIMITER_TYPE_INFO] # choices for Form
DELIMITER_VALUE_LOOKUP = dict( (dt['varname'], dt['value']) for dt in DELIMITER_TYPE_INFO)  # value look up for form "clean"
DEFAULT_DELIMITER = DELIMITER_TYPE_INFO[0]['varname']   # form default value

class UploadDataTableForm(forms.Form):
    title = forms.CharField(max_length=255)
    uploaded_file = forms.FileField()
    delimiter_type = forms.ChoiceField(choices=DELIMITER_TYPE_CHOICES, initial=DEFAULT_DELIMITER, required=False)
    no_header_row = forms.BooleanField(initial=False, required=False) 

    def clean_delimiter_type(self):
        """
        Return actual delimiter value.  e.g. form may have "COMMA" but return ","
        """
        delim = self.cleaned_data.get('delimiter_type', None)
        if delim is None or len(delim) ==0:
            # If no delim is specified, default to a comma
            delim_value = DELIMITER_VALUE_LOOKUP.get(DEFAULT_DELIMITER, None) 
        else:
            delim_value = DELIMITER_VALUE_LOOKUP.get(delim, None)
        if delim_value is None:
            raise forms.ValidationError(_('Invalid value'))

        return delim_value
