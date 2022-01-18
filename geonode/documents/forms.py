#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from geonode.base.forms import ResourceBaseForm
import os
import re
import json
import logging

from modeltranslation.forms import TranslationModelForm

from django import forms
from django.conf import settings
from django.forms import HiddenInput
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import filesizeformat

from geonode.maps.models import Map
from geonode.layers.models import Dataset
from geonode.resource.utils import get_related_resources
from geonode.documents.models import (
    Document,
    DocumentResourceLink)
from geonode.upload.models import UploadSizeLimit

logger = logging.getLogger(__name__)


class SizeRestrictedFileField(forms.FileField):
    """
    Same as FileField, but checks file max_size based on the value stored on `field_slug`.
        * field_slug - a slug indicating the database object from where the max_size will be retrieved.
    """
    def __init__(self, *args, **kwargs):
        self.field_slug = kwargs.pop("field_slug")
        super(SizeRestrictedFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(SizeRestrictedFileField, self).clean(*args, **kwargs)
        if data is None:
            return data
        file_size = self._get_file_size(data)
        if file_size is not None:
            # Only query the DB for a max_size when there is a file_size
            max_size = self._get_max_size()
            # Validate
            if file_size is not None and file_size > max_size:
                raise forms.ValidationError(_(
                    f'File size size exceeds {filesizeformat(max_size)}. Please try again with a smaller file.'
                ))
        return data

    def _get_file_size(self, data):
        try:
            file_size = data.size
        except AttributeError:
            file_size = None
        return file_size

    def _get_max_size(self):
        try:
            max_size_db_obj = UploadSizeLimit.objects.get(slug=self.field_slug)
        except UploadSizeLimit.DoesNotExist:
            max_size_db_obj = UploadSizeLimit.objects.create_default_limit_with_slug(slug=self.field_slug)
        return max_size_db_obj.max_size


class DocumentFormMixin:

    def generate_link_choices(self, resources=None):

        if resources is None:
            resources = list(Dataset.objects.all())
            resources += list(Map.objects.all())
            resources.sort(key=lambda x: x.title)

        choices = []
        for obj in resources:
            type_id = ContentType.objects.get_for_model(obj.__class__).id
            choices.append([
                f"type:{type_id}-id:{obj.id}",
                f"{obj.title} ({obj.polymorphic_ctype.model})"
            ])

        return choices

    def generate_link_values(self, resources=None):
        choices = self.generate_link_choices(resources=resources)
        return [choice[0] for choice in choices]

    def save_many2many(self, links_field='links'):
        # create and fetch desired links
        instances = []
        for link in self.cleaned_data[links_field]:
            matches = re.match(r"type:(\d+)-id:(\d+)", link)
            if matches:
                content_type = ContentType.objects.get(id=matches.group(1))
                instance, _ = DocumentResourceLink.objects.get_or_create(
                    document=self.instance,
                    content_type=content_type,
                    object_id=matches.group(2),
                )
                instances.append(instance)

        # delete remaining links
        DocumentResourceLink.objects\
            .filter(document_id=self.instance.id).exclude(pk__in=[i.pk for i in instances]).delete()


class DocumentForm(ResourceBaseForm, DocumentFormMixin):

    title = forms.CharField(required=False)

    links = forms.MultipleChoiceField(
        label=_("Link to"),
        required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['links'].choices = self.generate_link_choices()
        self.fields['links'].initial = self.generate_link_values(
            resources=get_related_resources(self.instance)
        )
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update(
                    {
                        'class': 'has-external-popover',
                        'data-content': help_text,
                        'placeholder': help_text,
                        'data-placement': 'right',
                        'data-container': 'body',
                        'data-html': 'true'
                    }
                )

    class Meta(ResourceBaseForm.Meta):
        model = Document
        exclude = ResourceBaseForm.Meta.exclude + (
            'content_type',
            'object_id',
            'doc_file',
            'extension',
            'subtype',
            'doc_url')


class DocumentDescriptionForm(forms.Form):
    title = forms.CharField(max_length=300)
    abstract = forms.CharField(max_length=2000, widget=forms.Textarea, required=False)
    keywords = forms.CharField(max_length=500, required=False)


class DocumentCreateForm(TranslationModelForm, DocumentFormMixin):

    """
    The document upload form.
    """
    permissions = forms.CharField(
        widget=HiddenInput(
            attrs={
                'name': 'permissions',
                'id': 'permissions'}),
        required=True)

    links = forms.MultipleChoiceField(
        label=_("Link to"),
        required=False)

    doc_file = SizeRestrictedFileField(
        label=_("File"),
        required=False,
        field_slug="document_upload_size"
    )

    class Meta:
        model = Document
        fields = ['title', 'doc_file', 'doc_url']
        widgets = {
            'name': HiddenInput(attrs={'cols': 80, 'rows': 20}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['links'].choices = self.generate_link_choices()

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
        cleaned_data = super().clean()
        doc_file = self.cleaned_data.get('doc_file')
        doc_url = self.cleaned_data.get('doc_url')

        if not doc_file and not doc_url and "doc_file" not in self.errors and "doc_url" not in self.errors:
            logger.error("Document must be a file or url.")
            raise forms.ValidationError(_("Document must be a file or url."))

        if doc_file and doc_url:
            logger.error("A document cannot have both a file and a url.")
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
            logger.debug("This file type is not allowed")
            raise forms.ValidationError(_("This file type is not allowed"))

        return doc_file
