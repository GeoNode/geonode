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
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from owslib.util import clean_ows_url

from geonode.utils import is_safe_url

WMS_VERSIONS = ("1.3.0", "1.1.1")


class WmsConnectionSerializer(serializers.Serializer):
    """Connection parameters of an OGC WMS: validates the AuthConfig payload and describes it to the UI"""

    url = serializers.URLField(label=_("Service URL"))
    version = serializers.ChoiceField(label=_("Version"), choices=WMS_VERSIONS, default="1.3.0")
    username = serializers.CharField(label=_("Username"), required=False)
    # spaces are part of a password
    password = serializers.CharField(
        label=_("Password"), trim_whitespace=False, required=False, style={"input_type": "password"}
    )

    def validate_url(self, value):
        # same check every request repeats: http(s) only, no credentials in the url, no private or local host
        if not is_safe_url(value):
            raise serializers.ValidationError(_("Enter a public http or https URL, without credentials."))
        # vendor parameters (e.g. map=) are kept, service, request and version are set by the provider
        return clean_ows_url(value)

    def validate(self, attrs):
        if bool(attrs.get("username")) != bool(attrs.get("password")):
            raise serializers.ValidationError(_("Provide both username and password, or none."))
        return attrs
