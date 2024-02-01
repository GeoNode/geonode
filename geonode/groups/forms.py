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
from django.utils.translation import gettext_lazy as _
from modeltranslation.forms import TranslationModelForm

from django.contrib.auth import get_user_model
from django_select2.forms import Select2MultipleWidget

from geonode.groups.models import GroupProfile
from geonode.people.utils import get_available_users


class GroupForm(TranslationModelForm):
    slug = forms.SlugField(
        help_text=_("a short version of the name consisting only of letters, numbers, underscores and hyphens."),
        widget=forms.HiddenInput,
        required=False,
    )

    def clean_slug(self):
        if GroupProfile.objects.filter(slug__iexact=self.cleaned_data["slug"]).exists():
            raise forms.ValidationError(_("A group already exists with that slug."))
        return self.cleaned_data["slug"].lower()

    def clean_title(self):
        if GroupProfile.objects.filter(title__iexact=self.cleaned_data["title"]).exists():
            raise forms.ValidationError(_("A group already exists with that name."))
        return self.cleaned_data["title"]

    def clean(self):
        cleaned_data = self.cleaned_data

        name = cleaned_data.get("title")
        if not name or GroupProfile.objects.filter(title__iexact=self.cleaned_data["title"]).exists():
            raise forms.ValidationError(_("A group already exists with that name."))
        slug = slugify(name)
        if not slug or GroupProfile.objects.filter(slug__iexact=self.cleaned_data["slug"]).exists():
            raise forms.ValidationError(_("A group already exists with that slug."))
        cleaned_data["slug"] = slug

        return cleaned_data

    class Meta:
        model = GroupProfile
        exclude = ["group"]


class GroupUpdateForm(forms.ModelForm):
    def clean_name(self):
        if GroupProfile.objects.filter(name__iexact=self.cleaned_data["title"]).exists():
            if self.cleaned_data["title"] == self.instance.name:
                pass  # same instance
            else:
                raise forms.ValidationError(_("A group already exists with that name."))
        return self.cleaned_data["title"]

    class Meta:
        model = GroupProfile
        exclude = ["group"]


class GroupMemberForm(forms.Form):
    def __init__(self, *args, **kwargs):
        """Grants access to the request object so that only members of the current user
        are given as options"""
        _user = None
        if isinstance(args[0], get_user_model()):
            _user = args[0]
            args = args[1:]
        super(forms.Form, self).__init__(*args, **kwargs)
        if _user:
            self.fields["user_identifiers"].queryset = get_available_users(_user).order_by("username")
        else:
            self.fields["user_identifiers"].queryset = None

    user_identifiers = forms.ModelMultipleChoiceField(
        required=True, queryset=None, label=_("User Identifiers"), widget=Select2MultipleWidget
    )

    manager_role = forms.BooleanField(required=False, label=_("Assign manager role"))

    def clean_user_identifiers(self):
        new_members = []
        errors = []
        for user in self.cleaned_data["user_identifiers"]:
            try:
                new_members.append(user)
            except get_user_model().DoesNotExist:
                errors.append(user)
        if errors:
            raise forms.ValidationError(
                _("The following are not valid usernames: %(errors)s; " "not added to the group"),
                params={"errors": ", ".join(errors)},
            )
        return new_members
