from django import forms
from django.core.validators import MaxValueValidator, RegexValidator
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import DataTable, TableJoin, TableJoinResult, TABLE_JOIN_TO_RESULT_MAP

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
    """
    Used to validate DataTable upload requests
    """
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


class DataTableUploadFormLatLng(DataTableUploadForm):
    """
    Used to validate DataTable upload requests with Longitude/Latitude Columns
    """
    lng_attribute = forms.CharField(help_text='Longitude column name')
    lat_attribute = forms.CharField(help_text='Latitude column name')



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

    @staticmethod
    def getDataTableAsJson(data_table):
        """
        For API call geonode.contrib.datatables.views.datatable_detail
        """
        assert isinstance(data_table, DataTable), "data_table must be a DataTable object"
        assert data_table.id is not None,\
            "This DataTable does not have an 'id'.  Please save it before calling" \
            " 'as_json()'"

        # Using form to help flag errors if WorldMap and/or GeoConnect change this data
        #
        f = DataTableResponseForm(data_table.__dict__)
        if not f.is_valid():
            err_msg = "Calling .as_json on DataTable object (id:%s) failed.  Validator" \
                      " errors with DataTableResponseForm:\n %s" % (data_table.id, f.errors)
            raise ValueError(err_msg)

        json_info = f.cleaned_data
        json_info['attributes'] = data_table.attributes_as_json()
        return json_info


class TableJoinResultForm(forms.ModelForm):
    """
    Used to validate incoming from WorldMap
    """
    class Meta:
        model = TableJoinResult


    @staticmethod
    def get_cleaned_data_from_table_join(table_join):
        """
        Given a WorldMap TableJoin* object:
            - Evaluate it against the TableJoinResultForm
            - Return the form's cleaned_data

        Method used to return WorldMap join results--expected to evaluate cleanly
            e.g. It works or throws an assertion error
        """
        if not isinstance(table_join, TableJoin):
            raise ValueError("table_join must be TableJoin object")

        f = TableJoinResultForm.create_form_from_table_join(table_join)

        assert f.is_valid(), "Data for TableJoinResultForm is not valid.  \nErrors:%s" % f.errors()

        return f.cleaned_data

    @staticmethod
    def create_form_from_table_join(table_join):
        """
        Format parameters TableJoin object
        """
        assert isinstance(table_join, TableJoin), "table_join must be TableJoin object"

        # ----------------------------------------------------------------------
        # Iterate through the dict linking TableJoin attributes
        #   to TableJoinResult fields
        #
        # ----------------------------------------------------------------------
        params = {}
        for new_key, attr_name in TABLE_JOIN_TO_RESULT_MAP.items():
            # ----------------------------------------------------------------------
            # Make sure the table_join object has all the appropriate attributes
            #
            #   e.g. This should blow up if the TableJoin object changes in the future
            #       and doesn't have the required attributes
            # ----------------------------------------------------------------------
            #print 'new_key/attr_name', new_key, attr_name
            attr_parts = attr_name.split('.')
            for idx in range(0, len(attr_parts)):
                obj_name = '.'.join(['table_join',] + attr_parts[0:idx] )
                #print 'check: %s - %s' % (obj_name, attr_parts[idx])
                assert hasattr(eval(obj_name), attr_parts[idx])\
                        , '%s object does not have a "%s" attribute.' % (obj_name, attr_parts[idx])

            # ----------------------------------------------------------------------
            # Add the attribute to the params dict
            # ----------------------------------------------------------------------
            param_val = eval('table_join.%s' % (attr_name))
            if hasattr(param_val, '__call__'):
                # We want the result of the function, e.g. join_layer.get_absolute_url
                params[new_key] = param_val.__call__()
            else:
                params[new_key] = param_val

        print 'params', params
        return TableJoinResultForm(params)

"""
lat lng result form
TABLE_JOIN_TO_RESULT_MAP = dict(tablejoin_id='pk',
                             tablejoin_view_name='view_name',
                             join_layer_id='join_layer.id',
                             join_layer_typename='join_layer.typename',
                             join_layer_url='join_layer.get_absolute_url',
                             matched_record_count='matched_records_count',
                             unmatched_record_count='unmatched_records_count',
                             unmatched_records_list='unmatched_records_list',
                             table_id='datatable.id',
                             table_name='datatable.table_name',
                             table_join_attribute='table_attribute.attribute',
                             layer_typename='join_layer.typename',
                             layer_join_attribute='layer_attribute.attribute')
"""
