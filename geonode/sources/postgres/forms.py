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
from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

POSTGRES_SSLMODES = ("disable", "allow", "prefer", "require", "verify-ca", "verify-full")


class PostgresConnectionForm(forms.Form):
    """Connection parameters of a PostgreSQL source: validates the AuthConfig payload and describes it to the UI"""

    host = forms.CharField(label=_("Host"))
    port = forms.IntegerField(label=_("Port"), min_value=1, max_value=65535, initial=5432, required=False)
    database = forms.CharField(label=_("Database"))
    username = forms.CharField(label=_("Username"))
    # spaces are part of a password
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput, strip=False)
    sslmode = forms.ChoiceField(
        label=_("SSL mode"),
        choices=[(mode, mode) for mode in POSTGRES_SSLMODES],
        initial="prefer",
        required=False,
    )
    # OGR splits the schema list on commas
    schema = forms.CharField(
        label=_("Schema"),
        initial="public",
        required=False,
        validators=[RegexValidator(r"^[^,]+$", _("Enter a single schema name."))],
    )

    def clean_port(self):
        return self.cleaned_data["port"] or 5432

    def clean_sslmode(self):
        return self.cleaned_data["sslmode"] or "prefer"

    def clean_schema(self):
        return self.cleaned_data["schema"] or "public"
