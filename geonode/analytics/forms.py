 
import taggit
from django import forms
from geonode.analytics.models import Analysis
from geonode.people.models import Profile
from django.utils.translation import ugettext_lazy as _


class AnalysisForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.SplitDateTimeWidget)
    date.widget.widgets[0].attrs = {"class":"datepicker", 'data-date-format': "yyyy-mm-dd"}
    date.widget.widgets[1].attrs = {"class":"time"}
    temporal_extent_start = forms.DateField(required=False,widget=forms.DateInput(attrs={"class":"datepicker", 'data-date-format': "yyyy-mm-dd"}))
    temporal_extent_end = forms.DateField(required=False,widget=forms.DateInput(attrs={"class":"datepicker", 'data-date-format': "yyyy-mm-dd"}))
    poc = forms.ModelChoiceField(empty_label = "Person outside GeoNode (fill form)",
                                 label = "Point Of Contact", required=False,
                                 queryset = Profile.objects.exclude(user=None))

    metadata_author = forms.ModelChoiceField(empty_label = "Person outside GeoNode (fill form)",
                                             label = "Metadata Author", required=False,
                                             queryset = Profile.objects.exclude(user=None))
    keywords = taggit.forms.TagField(required=False,
                                     help_text=_("A space or comma-separated list of keywords"))
    class Meta:
        model = Analysis
        exclude = ('contacts', 'zoom', 'projection', 'center_x', 'center_y', 'uuid',
                   'bbox_x0', 'bbox_x1', 'bbox_y0', 'bbox_y1', 'srid',
                   'csw_typename', 'csw_schema', 'csw_mdsource', 'csw_type',
                   'csw_wkt_geometry', 'metadata_uploaded', 'metadata_xml', 'csw_anytext',
                   'popular_count', 'share_count', 'thumbnail')
        widgets = {
            'abstract': forms.Textarea(attrs={'cols': 40, 'rows': 10}),
        }


