from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.validators import MaxValueValidator


MAX_ALLOWED_YEAR = 9999
ERR_MSG_START_YEAR_CANNOT_BE_GREATER = "The start year cannot be greater than the end year."
ERR_MSG_YEAR_TOO_HIGH = 'Ensure this value is less than or equal to %d.' % (MAX_ALLOWED_YEAR)


class JoinTargetForm(forms.Form):

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
