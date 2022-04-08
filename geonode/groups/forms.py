#########################################################################
#
# Copyright (C) 2017 OSGeo
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

from django import forms
from slugify import slugify
from django.utils.translation import ugettext as _
from modeltranslation.forms import TranslationModelForm

from django.contrib.auth import get_user_model

from geonode.groups.models import GroupProfile


class GroupForm(TranslationModelForm):

    slug = forms.SlugField(
        help_text=_("a short version of the name consisting only of letters, numbers, underscores and hyphens."),
        widget=forms.HiddenInput,
        required=False)

    def clean_slug(self):
        if GroupProfile.objects.filter(
                slug__iexact=self.cleaned_data["slug"]).exists():
            raise forms.ValidationError(
                _("A group already exists with that slug."))
        return self.cleaned_data["slug"].lower()

    def clean_title(self):
        if GroupProfile.objects.filter(
                title__iexact=self.cleaned_data["title"]).exists():
            raise forms.ValidationError(
                _("A group already exists with that name."))
        return self.cleaned_data["title"]

    def clean(self):
        cleaned_data = self.cleaned_data

        name = cleaned_data.get("title")
        if not name or GroupProfile.objects.filter(title__iexact=self.cleaned_data["title"]).exists():
            raise forms.ValidationError(
                _("A group already exists with that name."))
        slug = slugify(name)
        if not slug or GroupProfile.objects.filter(slug__iexact=self.cleaned_data["slug"]).exists():
            raise forms.ValidationError(
                _("A group already exists with that slug."))
        cleaned_data["slug"] = slug

        return cleaned_data

    class Meta:
        model = GroupProfile
        exclude = ['group']


class GroupUpdateForm(forms.ModelForm):

    def clean_name(self):
        if GroupProfile.objects.filter(
                name__iexact=self.cleaned_data["title"]).exists():
            if self.cleaned_data["title"] == self.instance.name:
                pass  # same instance
            else:
                raise forms.ValidationError(
                    _("A group already exists with that name."))
        return self.cleaned_data["title"]

    class Meta:
        model = GroupProfile
        exclude = ['group']


class GroupMemberForm(forms.Form):
    user_identifiers = forms.CharField(
        label=_("User Identifiers"),
        widget=forms.SelectMultiple(
            attrs={
                'class': 'user-select',
                'style': 'width:300px'
            }
        )
    )
    manager_role = forms.BooleanField(
        required=False,
        label=_("Assign manager role")
    )

    def clean_user_identifiers(self):
        values = self.cleaned_data['user_identifiers'].strip('][').split(', ')
        new_members = []
        errors = []
        for name in (v.strip('\'') for v in values):
            try:
                new_members.append(get_user_model().objects.get(username=name))
            except get_user_model().DoesNotExist:
                errors.append(name)
        if errors:
            raise forms.ValidationError(
                _("The following are not valid usernames: %(errors)s; "
                  "not added to the group"),
                params={
                    "errors": ", ".join(errors)
                }
            )
        return new_members
