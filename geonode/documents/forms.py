import taggit

from django import forms
from django.utils.translation import ugettext_lazy as _

from geonode.people.models import Profile
from geonode.documents.models import Document

class DocumentForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.SplitDateTimeWidget)
    date.widget.widgets[0].attrs = {"class":"date"}
    date.widget.widgets[1].attrs = {"class":"time"}
    temporal_extent_start = forms.DateField(required=False,widget=forms.DateInput(attrs={"class":"date"}))
    temporal_extent_end = forms.DateField(required=False,widget=forms.DateInput(attrs={"class":"date"}))

    poc = forms.ModelChoiceField(empty_label = "Person outside GeoNode (fill form)",
                                 label = "Point Of Contact", required=False,
                                 queryset = Profile.objects.exclude(user=None))

    metadata_author = forms.ModelChoiceField(empty_label = "Person outside GeoNode (fill form)",
                                             label = "Metadata Author", required=False,
                                             queryset = Profile.objects.exclude(user=None))
    keywords = taggit.forms.TagField(required=False,
                                     help_text=_("A space or comma-separated list of keywords"))
    class Meta:
        model = Document
        exclude = ('contacts','workspace', 'store', 'name', 'uuid', 'storeType', 'typename',
                   'bbox_x0', 'bbox_x1', 'bbox_y0', 'bbox_y1', 'srid',
                   'csw_typename', 'csw_schema', 'csw_mdsource', 'csw_type',
                   'csw_wkt_geometry', 'metadata_uploaded', 'metadata_xml', 'csw_anytext', 
                   'content_type', 'object_id', 'doc_file', 'extension')

class DocumentDescriptionForm(forms.Form):
    title = forms.CharField(300)
    abstract = forms.CharField(1000, widget=forms.Textarea, required=False)
    keywords = forms.CharField(500, required=False)