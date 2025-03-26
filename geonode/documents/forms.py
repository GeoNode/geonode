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

import os
import json
import logging

from modeltranslation.forms import TranslationModelForm

from django import forms
from django.conf import settings
from django.forms import HiddenInput
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat

from geonode.base.forms import ResourceBaseForm, get_tree_data
from geonode.documents.models import Document
from geonode.upload.models import UploadSizeLimit
from geonode.upload.api.exceptions import FileUploadLimitException

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
                raise FileUploadLimitException(
                    _(f"File size size exceeds {filesizeformat(max_size)}. Please try again with a smaller file.")
                )
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


class DocumentForm(ResourceBaseForm):
    title = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["regions"].choices = get_tree_data()
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != "":
                self.fields[field].widget.attrs.update(
                    {
                        "class": "has-external-popover",
                        "data-content": help_text,
                        "placeholder": help_text,
                        "data-placement": "right",
                        "data-container": "body",
                        "data-html": "true",
                    }
                )

    class Meta(ResourceBaseForm.Meta):
        model = Document
        exclude = ResourceBaseForm.Meta.exclude + (
            "content_type",
            "object_id",
            "doc_file",
            "extension",
            "subtype",
            "doc_url",
        )


class DocumentDescriptionForm(forms.Form):
    title = forms.CharField(max_length=300)
    abstract = forms.CharField(max_length=2000, widget=forms.Textarea, required=False)
    keywords = forms.CharField(max_length=500, required=False)


class DocumentCreateForm(TranslationModelForm):
    """
    The document upload form.
    """

    permissions = forms.CharField(
        widget=HiddenInput(attrs={"name": "permissions", "id": "permissions"}), required=False
    )

    doc_file = SizeRestrictedFileField(label=_("File"), required=False, field_slug="document_upload_size")

    class Meta:
        model = Document
        fields = ["title", "doc_file", "doc_url", "extension"]
        widgets = {
            "name": HiddenInput(attrs={"cols": 80, "rows": 20}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_permissions(self):
        """
        Ensures the JSON field is JSON.
        """
        permissions = self.cleaned_data["permissions"]

        if not self.fields["permissions"].required and (permissions is None or permissions == ""):
            return None

        try:
            return json.loads(permissions)
        except ValueError:
            raise forms.ValidationError(_("Permissions must be valid JSON."))

    def clean(self):
        """
        Ensures the doc_file or the doc_url field is populated.
        """
        cleaned_data = super().clean()
        doc_file = self.cleaned_data.get("doc_file")
        doc_url = self.cleaned_data.get("doc_url")
        extension = self.cleaned_data.get("extension")

        if not doc_file and not doc_url and "doc_file" not in self.errors and "doc_url" not in self.errors:
            logger.error("Document must be a file or url.")
            raise forms.ValidationError(_("Document must be a file or url."))

        if doc_file and doc_url:
            logger.error("A document cannot have both a file and a url.")
            raise forms.ValidationError(_("A document cannot have both a file and a url."))

        if extension:
            cleaned_data["extension"] = extension.replace(".", "").lower()

        return cleaned_data

    def clean_doc_file(self):
        """
        Ensures the doc_file is valid.
        """
        doc_file = self.cleaned_data.get("doc_file")

        if doc_file and not os.path.splitext(doc_file.name)[1].lower()[1:] in settings.ALLOWED_DOCUMENT_TYPES:
            logger.debug("This file type is not allowed")
            raise forms.ValidationError(_("This file type is not allowed"))

        return doc_file


class DocumentReplaceForm(forms.ModelForm):
    """
    The form used to replace a document.
    """

    doc_file = SizeRestrictedFileField(label=_("File"), required=True, field_slug="document_upload_size")

    class Meta:
        model = Document
        fields = ["doc_file"]

    def clean(self):
        """
        Ensures the doc_file field is populated.
        """
        cleaned_data = super().clean()
        doc_file = self.cleaned_data.get("doc_file")

        if not doc_file:
            raise forms.ValidationError(_("Document must be a file."))

        return cleaned_data

    def clean_doc_file(self):
        """
        Ensures the doc_file is valid.
        """
        doc_file = self.cleaned_data.get("doc_file")

        if doc_file and not os.path.splitext(doc_file.name)[1].lower()[1:] in settings.ALLOWED_DOCUMENT_TYPES:
            raise forms.ValidationError(_("This file type is not allowed"))

        return doc_file
