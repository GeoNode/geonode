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
from django.utils.translation import gettext_lazy as _

from owslib.util import clean_ows_url

from geonode.utils import is_safe_url

WMS_VERSIONS = ("1.3.0", "1.1.1")


class WmsConnectionForm(forms.Form):
    """Connection parameters of an OGC WMS: validates the AuthConfig payload and describes it to the UI"""

    url = forms.URLField(label=_("Service URL"), assume_scheme="https")
    version = forms.ChoiceField(
        label=_("Version"), choices=[(version, version) for version in WMS_VERSIONS], initial="1.3.0", required=False
    )
    username = forms.CharField(label=_("Username"), required=False)
    # spaces are part of a password
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput, strip=False, required=False)

    def clean_url(self):
        _url = self.cleaned_data["url"]
        # same check every request repeats: http(s) only, no credentials in the url, no private or local host
        if not is_safe_url(_url):
            raise forms.ValidationError(_("Enter a public http or https URL, without credentials."))
        # vendor parameters (e.g. map=) are kept, service, request and version are set by the provider
        return clean_ows_url(_url)

    def clean_version(self):
        return self.cleaned_data["version"] or "1.3.0"

    def clean(self):
        _data = super().clean()
        if bool(_data.get("username")) != bool(_data.get("password")):
            raise forms.ValidationError(_("Provide both username and password, or none."))
        return _data
