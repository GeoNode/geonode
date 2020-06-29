# -*- coding: utf-8 -*-
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

"""Profile extractor utilities for social account providers"""

from django.conf import settings


class BaseExtractor(object):
    """Base class for social account data extractors.

    In order to define new extractors you just need to define a class that
    implements:

    * Some of the method stubs defined below - you don't need to implement
      all of them, just use the ones you need;


    In the spirit of duck typing, your custom class does not even need to
    inherit from this one. As long as it provides the expected methods
    geonode should be able to use it.

    Be sure to let geonode know about any custom adapters that you define by
    updating the ``SOCIALACCOUNT_PROFILE_EXTRACTORS`` setting.

    """

    def extract_area(self, data):
        raise NotImplementedError

    def extract_city(self, data):
        raise NotImplementedError

    def extract_country(self, data):
        raise NotImplementedError

    def extract_delivery(self, data):
        raise NotImplementedError

    def extract_email(self, data):
        raise NotImplementedError

    def extract_fax(self, data):
        raise NotImplementedError

    def extract_first_name(self, data):
        raise NotImplementedError

    def extract_last_name(self, data):
        raise NotImplementedError

    def extract_organization(self, data):
        raise NotImplementedError

    def extract_position(self, data):
        raise NotImplementedError

    def extract_profile(self, data):
        raise NotImplementedError

    def extract_voice(self, data):
        raise NotImplementedError

    def extract_zipcode(self, data):
        raise NotImplementedError


class FacebookExtractor(BaseExtractor):

    def extract_email(self, data):
        return data.get("email", "")

    def extract_first_name(self, data):
        return data.get("first_name", "")

    def extract_last_name(self, data):
        return data.get("last_name", "")

    def extract_profile(self, data):
        return data.get("cover", "")


class LinkedInExtractor(BaseExtractor):

    def extract_email(self, data):
        try:
            element = data.get("elements")[0]
        except IndexError:
            email = ""
        else:
            email = element.get("handle~", {}).get("emailAddress", "")
        return email

    def extract_first_name(self, data):
        return self._extract_field("firstName", data)

    def extract_last_name(self, data):
        return self._extract_field("lastName", data)

    def _extract_field(self, name, data):
        current_language = settings.LANGUAGE_CODE
        localized_field_values = data.get(name, {}).get("localized", {})
        for locale, name in localized_field_values.items():
            split_locale = locale.partition("_")[0]
            if split_locale == current_language:
                result = name
                break
        else:  # try to return first one, if it exists
            try:
                result = list(localized_field_values.items())[0][-1]
            except IndexError:
                result = ""
        return result


class OpenIDExtractor(BaseExtractor):

    def extract_email(self, data):
        return data.get("email", "")

    def extract_first_name(self, data):
        return data.get("first_name", "")

    def extract_last_name(self, data):
        return data.get("last_name", "")

    def extract_country(self, data):
        country = data.get("country", "")
        if country:
            from geonode.base.enumerations import COUNTRIES
            for _cnt in COUNTRIES:
                if country == _cnt[1]:
                    country = _cnt[0]
                    break
        return country

    def extract_language(self, data):
        language = data.get("language", "")
        if language:
            from .languages import LANGUAGES
            for _cnt in LANGUAGES:
                if language == _cnt[1]:
                    language = _cnt[0]
                    break
        return language

    def extract_timezone(self, data):
        timezone = data.get("timezone", "")
        if timezone:
            from .timezones import TIMEZONES
            for _cnt in TIMEZONES:
                if timezone == _cnt[1]:
                    timezone = _cnt[0]
                    break
        return timezone

    def extract_city(self, data):
        return data.get("city", "")

    def extract_zipcode(self, data):
        return data.get("postal_code", "")

    def extract_organization(self, data):
        return data.get("organization", "")

    def extract_voice(self, data):
        return data.get("phone", "")

    def extract_groups(self, data):
        return data.get("groups", "")

    def extract_roles(self, data):
        return data.get("roles", "")

    def extract_keywords(self, data):
        return data.get("keywords", "")


def _get_latest_position(data):
    all_positions = data.get(
        "positions",
        {"values": []}
    )["values"]
    return all_positions[0] if any(all_positions) else None
