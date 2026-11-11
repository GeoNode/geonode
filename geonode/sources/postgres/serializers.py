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
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

POSTGRES_SSLMODES = ("disable", "allow", "prefer", "require", "verify-ca", "verify-full")


class PostgresConnectionSerializer(serializers.Serializer):
    """Connection parameters of a PostgreSQL source: validates the AuthConfig payload and describes it to the UI"""

    host = serializers.CharField(label=_("Host"))
    port = serializers.IntegerField(label=_("Port"), min_value=1, max_value=65535, default=5432)
    database = serializers.CharField(label=_("Database"))
    username = serializers.CharField(label=_("Username"))
    # spaces are part of a password
    password = serializers.CharField(label=_("Password"), trim_whitespace=False, style={"input_type": "password"})
    sslmode = serializers.ChoiceField(label=_("SSL mode"), choices=POSTGRES_SSLMODES, default="prefer")
    # OGR splits the schema list on commas
    schema = serializers.CharField(
        label=_("Schema"),
        default="public",
        validators=[RegexValidator(r"^[^,]+$", _("Enter a single schema name."))],
    )
