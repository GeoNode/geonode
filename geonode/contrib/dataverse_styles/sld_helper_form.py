"""
Format used to valid parameters from geoconnect that will be
sent to the SLD Reser service

Example of an SLD rest service url
 http://localhost:8000/gs/rest/sldservice/geonode:boston_social_disorder_pbl/classify.xml?
    attribute=Violence_4
	&method=equalInterval
	&intervals=5
	&ramp=Gray
	&startColor=%23FEE5D9
	&endColor=%23A50F15
	&reverse=
"""
if __name__ == '__main__':
    import os, sys
    DJANGO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(DJANGO_ROOT)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'

import re
from django import forms


"""
Note: Classify methods and Color Ramps names are from the GeoServer SLD REST service:

http://docs.geoserver.org/stable/en/user/community/sldservice/index.html#classify-vector-data
"""
CLASSIFY_METHODS = ['equalInterval', 'quantile', 'jenks', 'uniqueInterval']
CLASSIFY_METHOD_CHOICES = [(x, x) for x in CLASSIFY_METHODS]

COLOR_RAMPS = ['red', 'blue', 'gray', 'jet', 'random', 'custom']

LAYER_PARAM_NAME = 'layer_name'
REQUIRED_PARAM_NAMES = [LAYER_PARAM_NAME, 'attribute',
                        'method', 'intervals', 'ramp',
                        'reverse', 'start_color', 'end_color']


class SLDHelperForm(forms.Form):
    """
    Evaluate classification parameters to be used for a new layer style
    """
    layer_name = forms.CharField(max_length=255)
    attribute = forms.CharField(max_length=100)
    method = forms.ChoiceField(choices=CLASSIFY_METHOD_CHOICES)
    intervals = forms.IntegerField(required=False)
    ramp = forms.CharField(max_length=255)
    reverse = forms.BooleanField(initial=False, required=False)

    # camelcase naming convention used to match the outgoing url string
    startColor = forms.CharField(max_length=7, required=False)
    midColor = forms.CharField(max_length=7, required=False)
    endColor = forms.CharField(max_length=7, required=False)


    def get_url_params_dict(self):
        """
        Parameters used to build the url for the SLD Service

        # /rest/sldservice/geonode:boston_social_disorder_pbl/classify.xml?attribute=Violence_4&method=equalInterval&intervals=5&ramp=Gray&startColor=%23FEE5D9&endColor=%23A50F15&reverse=
        """
        if not self.is_valid():
            return None

        params = self.cleaned_data.copy()

        final_params = dict()

        # Exclude non-required fields if they don't have values
        # e.g. midColor
        #
        for key, val in params.items():
            if key in REQUIRED_PARAM_NAMES or val:
                final_params[key] = val
        return final_params


    def is_valid_hex_color_val(self, hex_color_val):
        if not hex_color_val:
            return False

        # hex color pattern
        pattern = '^#(?:[0-9a-fA-F]{3}){1,2}$'
        if re.match(pattern, hex_color_val):
            return True
        return False


    def clean_ramp(self):
        """Check  the color ramp against geoserver allowed values"""

        color_ramp = self.cleaned_data.get('ramp', None)

        if color_ramp is None:
            raise forms.ValidationError(\
                ("The color ramp is required."
                 " Valid values: %s") %\
                  ','.split(COLOR_RAMPS))

        color_ramp = color_ramp.lower()

        if not color_ramp in COLOR_RAMPS:
            raise forms.ValidationError(\
                ("The color ramp is not valid."
                 " Valid values: %s") %\
                  ','.split(COLOR_RAMPS))

        return color_ramp


    def clean_intervals(self):
        num_intervals = self.cleaned_data.get('intervals', -1)

        if not(type(num_intervals)) == int:
            raise forms.ValidationError("This number of intervals must be an integer: %s" % num_intervals)

        if num_intervals < 1:
            raise forms.ValidationError("This is not a valid number of intervals: %s" % num_intervals)

        return num_intervals


    def clean_startColor(self):
        """Make sure the color is valid hex value"""

        c = self.cleaned_data.get('startColor', None)
        if self.is_valid_hex_color_val(c) or c == '':
            return c
        raise forms.ValidationError("This is not a valid end color: %s" % c)


    def clean_endColor(self):
        """Make sure the color is valid hex value"""

        c = self.cleaned_data.get('endColor', '')
        if self.is_valid_hex_color_val(c) or c == '':
            return c
        raise forms.ValidationError("This is not a valid end color: %s" % c)

    def clean_midColor(self):
        """Make sure the color is valid hex value"""

        c = self.cleaned_data.get('midColor', '')

        if self.is_valid_hex_color_val(c) or c == '':
            return c

        return ''   # default is blank


    """def clean_method(self):
        method = self.cleaned_data.get('method', None)

        if not method in self.VALID_METHODS:
            raise forms.ValidationError("This is not a valid method: %s" % method)
        return method
    """

    def clean_reverse(self):
        """Reverse parameter for colors"""
        reverse = self.cleaned_data.get('reverse', None)

        if reverse == '':
            reverse = False

        if not reverse in (True, False):
            raise forms.ValidationError(\
                ('This is not a valid value for reverse'
                 ' (should be true or false): \"%s\"') % reverse)

        if reverse is True:
            return 'true'

        return ''   # default is blank


    def get_attribute_and_classification_method(self):
        """Return attribute and classification method values
        for error user messages
        """
        if not self.cleaned_data:
            return (None, None)

        return (self.cleaned_data.get('attribute'),
                self.cleaned_data.get('method'))

    def get_error_list(self):
        if not self.errors:
            return None

        fmt_err_list = []
        for err_info in self.errors.items():
            attribute_name, error_list = err_info
            for single_err in error_list:
                fmt_err_list.append('%s: %s' % (attribute_name, single_err))
        return fmt_err_list

    @staticmethod
    def get_style_error_message(attribute_name, classify_method):
        return ('Styling failed with Attribute "<b>%s</b>"'
                ' and Classification Method "<b>%s</b>".'
                ' Please try another Attribute'
                ' and/or Classification Method.') %\
                 (attribute_name, classify_method)

if __name__ == '__main__':
    d = dict(\
            layer_name='boston_social_disorder_pbl',
            attribute='Income',
            method='equalInterval',
            intervals=5,
            ramp='Gray',
            startColor='#FEE5D9',
            endColor='#A50F15',
            midColor='#ffcc00',
            reverse='')

    f = SLDHelperForm(d)

    if f.is_valid():
        print 'valid'
        print f.cleaned_data
        print f.get_url_params_dict()
    else:
        #print f.errors.items()
        for err_tuple in f.errors.items():
            field_name, err_list = err_tuple
            for err in err_list:
                print field_name, err
