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


class BaseExtractor(object):
    """Base class for social account data extractors.

    In order to define new extractors you just need to define a class that
    implements:

    * Some of the method stubs defined below - you don't need to implement
      all of them, just use the ones you need;

    * the ``PROVIDER`` class attribute,, which should be a string with the
      all lowercase name of the provider;

    In the spirit of duck typing, your custom class does not even need to
    inherit from this one. As long as it provides the expected methods and
    the ``PROVIDER`` attribute geonode should be able to use it.

    Be sure to let geonode know about any custom adapters that you define by
    updating the ``SOCIALACCOUNT_PROFILE_EXTRACTORS`` setting.

    """

    PROVDER = "provider_name"

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

    PROVIDER = "facebook"

    def extract_email(self, data):
        return data.get("email", "")

    def extract_first_name(self, data):
        return data.get("first_name", "")

    def extract_last_name(self, data):
        return data.get("last_name", "")

    def extract_profile(self, data):
        return data.get("cover", "")


class LinkedInExtractor(BaseExtractor):

    PROVIDER = "linkedin"

    def extract_email(self, data):
        return data.get("email-address", "")

    def extract_first_name(self, data):
        return data.get("first-name", "")

    def extract_last_name(self, data):
        return data.get("last-name", "")

    def extract_position(self, data):
        return data.get("positions", {}).get("position", {}).get("title", "")

    def extract_organization(self, data):
        return data.get("positions", {}).get(
            "position", {}).get("company", {}).get("name", "")

    def extract_profile(self, data):
        headline = data.get("headline", "")
        summary = data.get("summary", "")
        profile = "\n".join((headline, summary))
        return profile.strip()
