import taggit
import re

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from geonode.people.models import Profile
from geonode.documents.models import Document
from geonode.maps.models import Map
from geonode.layers.models import Layer

class DocumentForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.SplitDateTimeWidget)
    date.widget.widgets[0].attrs = {"class":"datepicker", 'data-date-format': "yyyy-mm-dd"}
    date.widget.widgets[1].attrs = {"class":"time"}
    temporal_extent_start = forms.DateField(required=False,widget=forms.DateInput(attrs={"class":"datepicker", 'data-date-format': "yyyy-mm-dd"}))
    temporal_extent_end = forms.DateField(required=False,widget=forms.DateInput(attrs={"class":"datepicker", 'data-date-format': "yyyy-mm-dd"}))
    
    resource = forms.ChoiceField(label='Link to')

    poc = forms.ModelChoiceField(empty_label = "Person outside GeoNode (fill form)",
                                 label = "Point Of Contact", required=False,
                                 queryset = Profile.objects.exclude(user=None))

    metadata_author = forms.ModelChoiceField(empty_label = "Person outside GeoNode (fill form)",
                                             label = "Metadata Author", required=False,
                                             queryset = Profile.objects.exclude(user=None))
    keywords = taggit.forms.TagField(required=False,
                                     help_text=_("A space or comma-separated list of keywords"))
    
    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        rbases = list(Layer.objects.all())
        rbases += list(Map.objects.all())
        rbases.sort(key=lambda x: x.title)
        rbases_choices = []
        for obj in rbases:
            type_id = ContentType.objects.get_for_model(obj.__class__).id
            obj_id = obj.id
            form_value = "type:%s-id:%s" % (type_id, obj_id)
            display_text = '%s (%s)' % (obj.title, obj.geonode_type)
            rbases_choices.append([form_value, display_text])
        self.fields['resource'].choices = rbases_choices
        self.fields['resource'].initial = 'type:%s-id:%s' % (
            self.instance.content_type.id, self.instance.object_id)
    
    def save(self, *args, **kwargs):
        resource = self.cleaned_data['resource']
        matches = re.match("type:(\d+)-id:(\d+)", resource).groups()
        contenttype_id = matches[0]
        object_id = matches[1]
        contenttype = ContentType.objects.get(id=contenttype_id)
        self.cleaned_data['content_type'] = contenttype_id
        self.cleaned_data['object_id'] = object_id
        self.instance.object_id = object_id
        self.instance.content_type = contenttype
        return super(DocumentForm, self).save(*args, **kwargs)
        
    class Meta:
        model = Document
        exclude = ('contacts','workspace', 'store', 'name', 'uuid', 'storeType',
                   'typename', 'bbox_x0', 'bbox_x1', 'bbox_y0', 'bbox_y1', 'srid',
                   'csw_typename', 'csw_schema', 'csw_mdsource', 'csw_type',
                   'csw_wkt_geometry', 'metadata_uploaded', 'metadata_xml', 'csw_anytext', 
                   'content_type', 'object_id', 'doc_file', 'extension', 
                   'popular_count', 'share_count', 'thumbnail')

class DocumentDescriptionForm(forms.Form):
    title = forms.CharField(300)
    abstract = forms.CharField(1000, widget=forms.Textarea, required=False)
    keywords = forms.CharField(500, required=False)
