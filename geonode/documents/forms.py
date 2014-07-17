import json
import os
import taggit
import re

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.forms import HiddenInput, TextInput
from modeltranslation.forms import TranslationModelForm

from mptt.forms import TreeNodeMultipleChoiceField

from geonode.people.models import Profile
from geonode.documents.models import Document
from geonode.maps.models import Map
from geonode.layers.models import Layer
from geonode.base.models import Region


class DocumentForm(TranslationModelForm):
    date = forms.DateTimeField(widget=forms.SplitDateTimeWidget)
    date.widget.widgets[0].attrs = {
        "class": "datepicker",
        'data-date-format': "yyyy-mm-dd"}
    date.widget.widgets[1].attrs = {"class": "time"}
    temporal_extent_start = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "datepicker",
                'data-date-format': "yyyy-mm-dd"}))
    temporal_extent_end = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "datepicker",
                'data-date-format': "yyyy-mm-dd"}))

    resource = forms.ChoiceField(label='Link to')

    poc = forms.ModelChoiceField(
        empty_label="Person outside GeoNode (fill form)",
        label="Point Of Contact",
        required=False,
        queryset=Profile.objects.exclude(
            username='AnonymousUser'))

    metadata_author = forms.ModelChoiceField(
        empty_label="Person outside GeoNode (fill form)",
        label="Metadata Author",
        required=False,
        queryset=Profile.objects.exclude(
            username='AnonymousUser'))

    keywords = taggit.forms.TagField(
        required=False,
        help_text=_("A space or comma-separated list of keywords"))

    regions = TreeNodeMultipleChoiceField(
        required=False,
        queryset=Region.objects.all(),
        level_indicator=u'___')
    regions.widget.attrs = {"size": 20}

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        rbases = list(Layer.objects.all())
        rbases += list(Map.objects.all())
        rbases.sort(key=lambda x: x.title)
        rbases_choices = []
        rbases_choices.append(['no_link', '---------'])
        for obj in rbases:
            type_id = ContentType.objects.get_for_model(obj.__class__).id
            obj_id = obj.id
            form_value = "type:%s-id:%s" % (type_id, obj_id)
            display_text = '%s (%s)' % (obj.title, obj.polymorphic_ctype.model)
            rbases_choices.append([form_value, display_text])
        self.fields['resource'].choices = rbases_choices
        if self.instance.content_type:
            self.fields['resource'].initial = 'type:%s-id:%s' % (
                self.instance.content_type.id, self.instance.object_id)

        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update(
                    {
                        'class': 'has-popover',
                        'data-content': help_text,
                        'data-placement': 'right',
                        'data-container': 'body',
                        'data-html': 'true'})

    def save(self, *args, **kwargs):
        contenttype_id = None
        contenttype = None
        object_id = None
        resource = self.cleaned_data['resource']
        if resource != 'no_link':
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
        exclude = (
            'uuid',
            'contacts',
            'workspace',
            'store',
            'name',
            'uuid',
            'storeType',
            'typename',
            'bbox_x0',
            'bbox_x1',
            'bbox_y0',
            'bbox_y1',
            'srid',
            'category',
            'csw_typename',
            'csw_schema',
            'csw_mdsource',
            'csw_type',
            'csw_wkt_geometry',
            'metadata_uploaded',
            'metadata_xml',
            'csw_anytext',
            'content_type',
            'object_id',
            'doc_file',
            'extension',
            'popular_count',
            'share_count',
            'thumbnail',
            'doc_url')


class DocumentDescriptionForm(forms.Form):
    title = forms.CharField(300)
    abstract = forms.CharField(1000, widget=forms.Textarea, required=False)
    keywords = forms.CharField(500, required=False)


class DocumentReplaceForm(forms.ModelForm):

    """
    The form used to replace a document.
    """

    class Meta:
        model = Document
        fields = ['doc_file', 'doc_url']

    def clean(self):
        """
        Ensures the doc_file or the doc_url field is populated.
        """
        cleaned_data = super(DocumentReplaceForm, self).clean()
        doc_file = self.cleaned_data.get('doc_file')
        doc_url = self.cleaned_data.get('doc_url')

        if not doc_file and not doc_url:
            raise forms.ValidationError(_("Document must be a file or url."))

        if doc_file and doc_url:
            raise forms.ValidationError(
                _("A document cannot have both a file and a url."))

        return cleaned_data

    def clean_doc_file(self):
        """
        Ensures the doc_file is valid.
        """
        doc_file = self.cleaned_data.get('doc_file')

        if doc_file and not os.path.splitext(
                doc_file.name)[1].lower()[
                1:] in settings.ALLOWED_DOCUMENT_TYPES:
            raise forms.ValidationError(_("This file type is not allowed"))

        return doc_file


class DocumentCreateForm(TranslationModelForm):

    """
    The document upload form.
    """
    permissions = forms.CharField(
        widget=HiddenInput(
            attrs={
                'name': 'permissions',
                'id': 'permissions'}),
        required=True)
    resource = forms.CharField(
        required=False,
        label=_("Link to"),
        widget=TextInput(
            attrs={
                'name': 'q',
                'id': 'resource'}))

    class Meta:
        model = Document
        fields = ['title', 'doc_file', 'doc_url']
        widgets = {
            'name': HiddenInput(attrs={'cols': 80, 'rows': 20}),
        }

    def clean_permissions(self):
        """
        Ensures the JSON field is JSON.
        """
        permissions = self.cleaned_data['permissions']

        try:
            return json.loads(permissions)
        except ValueError:
            raise forms.ValidationError(_("Permissions must be valid JSON."))

    def clean(self):
        """
        Ensures the doc_file or the doc_url field is populated.
        """
        cleaned_data = super(DocumentCreateForm, self).clean()
        doc_file = self.cleaned_data.get('doc_file')
        doc_url = self.cleaned_data.get('doc_url')

        if not doc_file and not doc_url:
            raise forms.ValidationError(_("Document must be a file or url."))

        if doc_file and doc_url:
            raise forms.ValidationError(
                _("A document cannot have both a file and a url."))

        return cleaned_data

    def clean_doc_file(self):
        """
        Ensures the doc_file is valid.
        """
        doc_file = self.cleaned_data.get('doc_file')

        if doc_file and not os.path.splitext(
                doc_file.name)[1].lower()[
                1:] in settings.ALLOWED_DOCUMENT_TYPES:
            raise forms.ValidationError(_("This file type is not allowed"))

        return doc_file
