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
import logging

from dal import autocomplete
from django import forms
from django.forms.fields import MultipleChoiceField
from django.utils.translation import gettext_lazy as _

from geonode.base.models import (
    ResourceBase,
)
from geonode.layers.models import Dataset

logger = logging.getLogger(__name__)


def get_user_choices():
    try:
        return [(x.pk, x.title) for x in Dataset.objects.all().order_by("id")]
    except Exception:
        return []


class UserAndGroupPermissionsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["layers"].label_from_instance = self.label_from_instance

    layers = MultipleChoiceField(
        choices=get_user_choices,
        widget=autocomplete.Select2Multiple(url="datasets_autocomplete"),
        label="Datasets",
        required=False,
    )

    permission_type = forms.ChoiceField(
        required=True,
        widget=forms.RadioSelect,
        choices=(
            ("view", "View"),
            ("download", "Download"),
            ("edit", "Edit"),
        ),
    )
    mode = forms.ChoiceField(
        required=True,
        widget=forms.RadioSelect,
        choices=(
            ("set", "Set"),
            ("unset", "Unset"),
        ),
    )
    ids = forms.CharField(required=False, widget=forms.HiddenInput())

    @staticmethod
    def label_from_instance(obj):
        return obj.title


class OwnerRightsRequestForm(forms.Form):
    resource = forms.ModelChoiceField(
        label=_("Resource"), queryset=ResourceBase.objects.all(), widget=forms.HiddenInput()
    )
    reason = forms.CharField(
        label=_("Reason"), widget=forms.Textarea, help_text=_("Short reasoning behind the request"), required=True
    )

    class Meta:
        fields = ["reason", "resource"]


class ThesaurusImportForm(forms.Form):
    rdf_file = forms.FileField()
