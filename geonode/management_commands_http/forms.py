from django import forms

from geonode.management_commands_http.models import ManagementCommandJob
from geonode.management_commands_http.utils.commands import (
    get_management_commands,
)


class ManagementCommandJobAdminForm(forms.ModelForm):
    autostart = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.available_commands = get_management_commands()
        self.fields["command"] = forms.ChoiceField(choices=[(command, command) for command in self.available_commands])

    class Meta:
        model = ManagementCommandJob
        fields = (
            "command",
            "args",
            "kwargs",
        )

    def clean_args(self):
        value = self.cleaned_data.get("args")

        if not isinstance(value, list):
            self.add_error("args", "args must be a list")

        if "--help" in value:
            self.add_error("args", 'Forbidden argument: "--help"')

        return value

    def clean_kwargs(self):
        value = self.cleaned_data.get("kwargs")

        if not isinstance(value, dict):
            self.add_error("kwargs", "kwargs must be a dict")

        return value
