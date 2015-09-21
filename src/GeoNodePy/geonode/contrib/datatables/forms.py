from django import forms
from django.core.validators import MaxValueValidator, RegexValidator
from django.core.files.uploadedfile import SimpleUploadedFile

MAX_ALLOWED_YEAR = 9999
ERR_MSG_START_YEAR_CANNOT_BE_GREATER = "The start year cannot be greater than the end year."
ERR_MSG_YEAR_TOO_HIGH = 'Ensure this value is less than or equal to %d.' % (MAX_ALLOWED_YEAR)

class JoinTargetForm(forms.Form):
    """
    Used to validate parameters passed to the views.jointargets API call
    """
    title = forms.CharField(required=False)
    type = forms.CharField(required=False)
    start_year = forms.IntegerField(label='Start Year', required=False, validators=[MaxValueValidator(MAX_ALLOWED_YEAR)])
    end_year = forms.IntegerField(required=False, validators=[MaxValueValidator(MAX_ALLOWED_YEAR)])

    def clean(self):
        cleaned_data = super(JoinTargetForm, self).clean()

        # Validate years if start and end years are specified
        #
        start_year = self.cleaned_data.get('start_year', None)
        end_year = self.cleaned_data.get('end_year', None)

        if start_year and end_year:
            if start_year > end_year:
                raise forms.ValidationError(ERR_MSG_START_YEAR_CANNOT_BE_GREATER)

        return cleaned_data

    def get_error_messages_as_html_string(self):
        assert hasattr(self, 'errors'), "Form must FAIL the 'is_valid()' check before calling this function"

        err_msgs = []
        for k, v in self.errors.items():
            if not k.startswith('_'):
                err_msgs.append('%s - %s' % (k, '<br />'.join(v)))
            else:
                err_msgs.append('<br />'.join(v))
        return '<br />'.join(err_msgs)


    def get_join_target_filter_kwargs(self):
        """
        Prepare kwargs for filtering JoinTarget objects
        :return:
        """
        assert hasattr(self, 'cleaned_data'), "Form must PASS the 'is_valid()' check before calling this function"

        # Init kwargs
        kwargs = {}

        # Title
        if self.cleaned_data.get('title'):
            kwargs['layer__title__icontains'] = self.cleaned_data['title']

        # Type
        if self.cleaned_data.get('type'):
            kwargs['geocode_type__name__icontains'] = self.cleaned_data['type']

        # Start year
        if self.cleaned_data.get('start_year'):
            kwargs['year__gte'] = self.cleaned_data['start_year']

        # End year
        if self.cleaned_data.get('end_year'):
            kwargs['year__lte'] = self.cleaned_data['end_year']

        return kwargs


class DataTableUploadForm(forms.Form):
    #        fields = ('title', 'abstract', 'delimiter', 'no_header_row')
    title = forms.CharField(max_length=255, help_text='Title for New DataTable')
    abstract = forms.CharField(widget=forms.Textarea, initial='(no abstract)')
    delimiter = forms.CharField(max_length=10, initial=',')
    no_header_row = forms.BooleanField(initial=False, required=False,
            help_text='Specify "True" if the first row is not a header')
    uploaded_file = forms.FileField()#upload_to='datatables/%Y/%m/%d')

    def clean_delimiter(self):
        """
        Return 1-string delimiter value.
        """
        delim_value = self.cleaned_data.get('delimiter', None)

        if delim_value is None:
            raise forms.ValidationError(_('Invalid value'))

        if len(delim_value) > 1:
            delim_value = delim_value[0]

        return str(delim_value)

class TableJoinRequestForm(forms.Form):

    table_name = forms.CharField(max_length=255, help_text='DataTable name')
    table_attribute = forms.CharField(max_length=255\
                                    , help_text='DataTable attribute name to join on')

    layer_name = forms.CharField(max_length=255, help_text='Layer name')
    layer_attribute = forms.CharField(max_length=255\
                                    , help_text='Layer attribute name to join on')



class TableUploadAndJoinRequestForm(DataTableUploadForm):
    """
    DataTableUploadForm + additional attributes
    """
    table_attribute = forms.CharField(max_length=255,
                                     help_text='DataTable attribute name to join on')
    layer_name = forms.CharField(max_length=255, help_text='Layer name')
    layer_attribute = forms.CharField(max_length=255,
                                    help_text='Layer attribute name to join on')



class DataTableResponseForm(forms.Form):
    """
    Response from the DataTable API
    """
    id = forms.IntegerField()
    title = forms.CharField()
    abstract = forms.CharField(widget=forms.Textarea, required=False)
    delimiter = forms.CharField()
    table_name = forms.CharField()
