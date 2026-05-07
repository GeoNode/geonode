#########################################################################
#
# Copyright (C) 2026 OSGeo
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
import json

from django import forms
from django.contrib import admin

from geonode.security.auth_registry import auth_handler_registry
from geonode.security.models import AuthConfig, URLPatternAuthConfig


def _get_auth_type_choices():
    if not auth_handler_registry.registry:
        auth_handler_registry.init_registry()
    return [(handled_type, handled_type) for handled_type in sorted(auth_handler_registry.registry.keys())]


class AuthConfigAdminForm(forms.ModelForm):
    type = forms.ChoiceField(choices=(), required=True)

    class Meta:
        model = AuthConfig
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = _get_auth_type_choices()
        current_type = getattr(self.instance, "type", None)
        if current_type and current_type not in {value for value, _ in choices}:
            choices = choices + [(current_type, current_type)]
        self.fields["type"].choices = choices
        if self.instance.pk and self.instance.payload:
            auth_handler_cls = auth_handler_registry.get_handler_class(current_type)
            if auth_handler_cls:
                self.initial["payload"] = json.dumps(auth_handler_cls.decrypt_payload(self.instance.payload))

    def clean(self):
        cleaned_data = super().clean()
        auth_type = cleaned_data.get("type")
        payload_value = cleaned_data.get("payload")
        if not auth_type or not payload_value:
            return cleaned_data

        if self.instance.pk and payload_value == self.instance.payload:
            # unchanged existing encrypted payload
            return cleaned_data

        auth_handler_cls = auth_handler_registry.get_handler_class(auth_type)
        if auth_handler_cls is None:
            raise forms.ValidationError(f"Unsupported auth config type '{auth_type}'")

        try:
            payload_dict = json.loads(payload_value)
        except json.JSONDecodeError:
            raise forms.ValidationError("Payload must be valid JSON.")

        auth_handler_cls.validate(payload_dict, instance=self.instance)
        self.cleaned_payload = payload_dict
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(self, "cleaned_payload"):
            auth_handler_cls = auth_handler_registry.get_handler_class(instance.type)
            instance.payload = auth_handler_cls.encrypt_payload(self.cleaned_payload)
        if commit:
            instance.save()
        return instance


@admin.register(AuthConfig)
class AuthConfigAdmin(admin.ModelAdmin):
    form = AuthConfigAdminForm
    list_display = ("id", "type")
    search_fields = ("type",)


@admin.register(URLPatternAuthConfig)
class URLPatternAuthConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "auth_config", "pattern")
    search_fields = ("pattern", "auth_config__type")
    raw_id_fields = ("auth_config",)
